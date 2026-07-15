# tests/test_documents.py
import uuid
from unittest.mock import patch

import pytest
import pytest_asyncio

from app.models.user import UserRole
from app.models.document import Documents


@pytest_asyncio.fixture
async def create_document_in_db(
    db_session,
    create_listing_in_db,
    create_contact_in_db,
    create_pipeline_in_db,
    create_user_in_db,
):
    async def _create(
        created_by=None, listing=None, contact=None, pipeline=None, **overrides
    ):
        if created_by is None:
            created_by = await create_user_in_db(
                email=f"doc-owner-{uuid.uuid4()}@test.com", role=UserRole.agent
            )
        if listing is None:
            listing = await create_listing_in_db()
        if contact is None:
            contact, _ = await create_contact_in_db()
        if pipeline is None:
            pipeline = await create_pipeline_in_db()

        defaults = {
            "id": uuid.uuid4(),
            "listing_id": listing.id,
            "contact_id": contact.id,
            "pipeline_id": pipeline.id,
            "created_by_id": created_by.id,
            "type": "listing_agreement",
            "file_path": f"/tmp/{uuid.uuid4()}.pdf",
            "generated_by": "manual",
            "status": "draft",
        }
        defaults.update(overrides)
        document = Documents(**defaults)
        db_session.add(document)
        await db_session.commit()
        await db_session.refresh(document)
        return document, created_by

    return _create


def _headers_for(user):
    from app.core.security import create_access_token

    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


# ---- GET /documents/{id} ----


@pytest.mark.asyncio
async def test_get_document_owner_can_access(client, create_document_in_db):
    document, owner = await create_document_in_db()
    response = await client.get(
        f"/documents/{document.id}", headers=_headers_for(owner)
    )
    assert response.status_code == 200
    assert response.json()["id"] == str(document.id)


@pytest.mark.asyncio
async def test_get_document_non_owner_forbidden(
    client, create_document_in_db, create_user_in_db
):
    document, owner = await create_document_in_db()
    other = await create_user_in_db(email="otherdoc@test.com", role=UserRole.agent)
    response = await client.get(
        f"/documents/{document.id}", headers=_headers_for(other)
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_document_admin_can_access_any(
    client, create_document_in_db, create_user_in_db
):
    document, owner = await create_document_in_db()
    admin = await create_user_in_db(email="docadmin@test.com", role=UserRole.admin)
    response = await client.get(
        f"/documents/{document.id}", headers=_headers_for(admin)
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_document_listing_agent_can_access(
    client, create_document_in_db, create_listing_in_db, create_user_in_db
):
    listing_agent = await create_user_in_db(
        email="listingagent@test.com", role=UserRole.agent
    )
    listing = await create_listing_in_db(agent=listing_agent)
    other_owner = await create_user_in_db(
        email="docowner2@test.com", role=UserRole.agent
    )
    document, _ = await create_document_in_db(created_by=other_owner, listing=listing)

    response = await client.get(
        f"/documents/{document.id}", headers=_headers_for(listing_agent)
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_document_contact_agent_can_access(
    client, create_document_in_db, create_contact_in_db, create_user_in_db
):
    contact, contact_agent = await create_contact_in_db()
    other_owner = await create_user_in_db(
        email="docowner3@test.com", role=UserRole.agent
    )
    document, _ = await create_document_in_db(created_by=other_owner, contact=contact)

    response = await client.get(
        f"/documents/{document.id}", headers=_headers_for(contact_agent)
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_document_not_found(client, create_user_in_db):
    user = await create_user_in_db(email="docnotfound@test.com", role=UserRole.agent)
    response = await client.get(
        f"/documents/{uuid.uuid4()}", headers=_headers_for(user)
    )
    assert response.status_code == 404


# ---- GET /documents/ (list, filtered not 403'd) ----


@pytest.mark.asyncio
async def test_list_documents_filters_to_accessible(
    client, create_document_in_db, create_user_in_db
):
    agent_a = await create_user_in_db(email="listdocsa@test.com", role=UserRole.agent)
    agent_b = await create_user_in_db(email="listdocsb@test.com", role=UserRole.agent)

    doc_a, _ = await create_document_in_db(created_by=agent_a)
    await create_document_in_db(created_by=agent_b)

    response = await client.get("/documents/", headers=_headers_for(agent_a))
    assert response.status_code == 200
    ids = [d["id"] for d in response.json()]
    assert str(doc_a.id) in ids
    assert len(ids) == 1


@pytest.mark.asyncio
async def test_list_documents_admin_sees_all(
    client, create_document_in_db, create_user_in_db
):
    agent_a = await create_user_in_db(email="listdocsc@test.com", role=UserRole.agent)
    agent_b = await create_user_in_db(email="listdocsd@test.com", role=UserRole.agent)
    admin = await create_user_in_db(email="listdocsadmin@test.com", role=UserRole.admin)

    await create_document_in_db(created_by=agent_a)
    await create_document_in_db(created_by=agent_b)

    response = await client.get("/documents/", headers=_headers_for(admin))
    assert response.status_code == 200
    assert len(response.json()) >= 2


@pytest.mark.asyncio
async def test_list_documents_type_filter(
    client, create_document_in_db, create_user_in_db
):
    agent = await create_user_in_db(email="listdocse@test.com", role=UserRole.agent)
    await create_document_in_db(created_by=agent, type="listing_agreement")
    await create_document_in_db(created_by=agent, type="disclosure")

    response = await client.get(
        "/documents/?type=disclosure", headers=_headers_for(agent)
    )
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["type"] == "disclosure"


# ---- GET /documents/{id}/download ----


@pytest.mark.asyncio
async def test_download_document_owner_can_access(
    client, create_document_in_db, tmp_path
):
    file_path = tmp_path / "test.pdf"
    file_path.write_bytes(b"%PDF-1.4 fake pdf content")

    document, owner = await create_document_in_db(file_path=str(file_path))

    response = await client.get(
        f"/documents/{document.id}/download", headers=_headers_for(owner)
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content == b"%PDF-1.4 fake pdf content"


@pytest.mark.asyncio
async def test_download_document_file_missing_returns_404(
    client, create_document_in_db
):
    document, owner = await create_document_in_db(
        file_path="/tmp/does-not-exist-" + str(uuid.uuid4()) + ".pdf"
    )

    response = await client.get(
        f"/documents/{document.id}/download", headers=_headers_for(owner)
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_download_document_non_owner_forbidden(
    client, create_document_in_db, create_user_in_db, tmp_path
):
    """Access check must run before the file-exists check / file read.
    A non-owner should get 403, not a 404 or a leaked file, and the file
    doesn't even need to exist on disk for this to hold.
    """
    document, owner = await create_document_in_db(
        file_path=str(tmp_path / "unreachable.pdf")
    )
    other = await create_user_in_db(email="downloadother@test.com", role=UserRole.agent)

    response = await client.get(
        f"/documents/{document.id}/download", headers=_headers_for(other)
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_download_document_not_found(client, create_user_in_db):
    user = await create_user_in_db(email="downloadnf@test.com", role=UserRole.agent)
    response = await client.get(
        f"/documents/{uuid.uuid4()}/download", headers=_headers_for(user)
    )
    assert response.status_code == 404


# ---- POST /documents/{id}/status ----


@pytest.mark.asyncio
async def test_update_document_status_non_owner_forbidden(
    client, create_document_in_db, create_user_in_db
):
    document, owner = await create_document_in_db(status="draft")
    other = await create_user_in_db(email="statusother@test.com", role=UserRole.agent)

    with patch("app.routers.documents.update_status") as mock_update_status:
        mock_update_status.return_value = document
        response = await client.post(
            f"/documents/{document.id}/status",
            json={"new_status": "sent"},
            headers=_headers_for(other),
        )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_document_status_not_found(client, create_user_in_db):
    user = await create_user_in_db(email="statusnf@test.com", role=UserRole.agent)

    with patch("app.routers.documents.update_status") as mock_update_status:
        mock_update_status.return_value = None
        response = await client.post(
            f"/documents/{uuid.uuid4()}/status",
            json={"new_status": "sent"},
            headers=_headers_for(user),
        )

    assert response.status_code == 404


# ---- POST /documents (generate) ----


@pytest.mark.asyncio
async def test_generate_document(
    client,
    create_listing_in_db,
    create_contact_in_db,
    create_pipeline_in_db,
    create_user_in_db,
):
    agent = await create_user_in_db(email="gendoc@test.com", role=UserRole.agent)
    listing = await create_listing_in_db()
    contact, _ = await create_contact_in_db()
    pipeline = await create_pipeline_in_db()

    with (
        patch(
            "app.services.document.render_template",
            return_value="<html></html>",
        ),
        patch("app.services.document.generate_pdf", return_value=b"%PDF-1.4 fake"),
        patch(
            "app.services.document.save_pdf_to_disk",
            return_value="/tmp/fake.pdf",
        ),
    ):
        response = await client.post(
            "/documents",
            json={
                "listing_id": str(listing.id),
                "contact_id": str(contact.id),
                "pipeline_id": str(pipeline.id),
                "type": "listing_agreement",
                "context": {},
            },
            headers=_headers_for(agent),
        )

    assert response.status_code == 200
    assert response.json()["type"] == "listing_agreement"
    assert response.json()["file_path"] == "/tmp/fake.pdf"
