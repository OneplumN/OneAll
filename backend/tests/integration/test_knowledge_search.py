import pytest
from rest_framework.test import APIClient

from apps.knowledge.models import KnowledgeArticle


@pytest.mark.django_db
def test_knowledge_search_filters_by_keyword_and_tag(django_user_model):
    user = django_user_model.objects.create_user(username="ops", password="Secret123")
    KnowledgeArticle.objects.create(
        title="证书续期操作流程",
        slug="certificate-renewal",
        category="运维",
        tags=["cert", "guide"],
        content="指导如何处理证书续期",
    )
    KnowledgeArticle.objects.create(
        title="探针故障排查",
        slug="probe-troubleshoot",
        category="探针",
        tags=["probe"],
        content="检查网络连通性和心跳。",
    )

    client = APIClient()
    client.force_authenticate(user)

    response = client.get("/api/knowledge/articles", {"keyword": "证书", "tag": "cert"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["slug"] == "certificate-renewal"
