from app.services.download_query_service import DownloadQueryService
from app.services.processing_queue import ProcessingJobOrigin, ProcessingJobStatus, ProcessingQueue


def _image_payload() -> dict[str, object]:
    return {
        "data": {
            "messageType": "imageMessage",
            "message": {
                "imageMessage": {
                    "fileName": "foto.jpg",
                    "mimetype": "image/jpeg",
                }
            },
        }
    }


def test_download_query_service_lists_jobs_like_desktop_queue() -> None:
    queue = ProcessingQueue()
    job = queue.enqueue(
        sender="5562999999999@s.whatsapp.net",
        origin=ProcessingJobOrigin.WHATSAPP,
        payload=_image_payload(),
    )

    response = DownloadQueryService(queue).list_jobs()

    assert response.total == 1
    assert response.items[0].short_id == job.id[:8]
    assert response.items[0].sender == "+55 62 99999-9999"
    assert response.items[0].origin == "WhatsApp"
    assert response.items[0].file == "foto.jpg"
    assert response.items[0].kind == "Imagem"
    assert response.items[0].status == "PENDENTE"


def test_download_query_service_clears_completed_jobs_only() -> None:
    queue = ProcessingQueue()
    completed = queue.enqueue("5562999999999@s.whatsapp.net", ProcessingJobOrigin.WHATSAPP, _image_payload())
    pending = queue.enqueue("5562888888888@s.whatsapp.net", ProcessingJobOrigin.WHATSAPP, _image_payload())
    completed.status = ProcessingJobStatus.COMPLETED
    queue.update(completed)

    response = DownloadQueryService(queue).clear_completed()

    assert response.removed == 1
    remaining = DownloadQueryService(queue).list_jobs().items
    assert [job.id for job in remaining] == [pending.id]
