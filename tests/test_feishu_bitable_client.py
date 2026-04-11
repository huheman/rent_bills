from types import SimpleNamespace

from app.clients.feishu_bitable import (
    FIELD_ELECTRICITY_PREV,
    FIELD_MONTH,
    FIELD_ROOM_NAME,
    FeishuBitableClient,
)


class _SearchResponse:
    def __init__(self, items, has_more=False, page_token=None) -> None:
        self.data = SimpleNamespace(items=items, has_more=has_more, page_token=page_token)

    def success(self) -> bool:
        return True


def test_search_by_month_does_not_require_room_name() -> None:
    requests = []

    class StubSearchApi:
        def search(self, request):
            requests.append(request)
            return _SearchResponse(
                [
                    SimpleNamespace(
                        record_id="rec_1",
                        fields={
                            FIELD_ROOM_NAME: [{"text": "201"}],
                            FIELD_MONTH: "2026年4月",
                            FIELD_ELECTRICITY_PREV: 1452,
                        },
                    )
                ]
            )

    client = FeishuBitableClient.__new__(FeishuBitableClient)
    client._settings = SimpleNamespace(feishu_table_app_token="app", feishu_table_id="tbl")
    client._client = SimpleNamespace(
        bitable=SimpleNamespace(
            v1=SimpleNamespace(app_table_record=StubSearchApi())
        )
    )

    result = client.search_by_month("2026年4月")

    conditions = requests[0].request_body.filter.conditions
    assert len(conditions) == 1
    assert conditions[0].field_name == FIELD_MONTH
    assert conditions[0].value == ["2026年4月"]
    assert result[0][FIELD_ROOM_NAME] == "201"
    assert result[0][FIELD_ELECTRICITY_PREV] == 1452


def test_search_by_month_adds_room_name_when_provided_and_paginates() -> None:
    requests = []

    class StubSearchApi:
        def search(self, request):
            requests.append(request)
            if len(requests) == 1:
                return _SearchResponse(
                    [
                        SimpleNamespace(
                            record_id="rec_1",
                            fields={
                                FIELD_ROOM_NAME: [{"text": "201"}],
                                FIELD_MONTH: "2026年4月",
                                FIELD_ELECTRICITY_PREV: 1452,
                            },
                        )
                    ],
                    has_more=True,
                    page_token="next-page",
                )
            return _SearchResponse(
                [
                    SimpleNamespace(
                        record_id="rec_2",
                        fields={
                            FIELD_ROOM_NAME: [{"text": "201"}],
                            FIELD_MONTH: "2026年4月",
                            FIELD_ELECTRICITY_PREV: 1460,
                        },
                    )
                ]
            )

    client = FeishuBitableClient.__new__(FeishuBitableClient)
    client._settings = SimpleNamespace(feishu_table_app_token="app", feishu_table_id="tbl")
    client._client = SimpleNamespace(
        bitable=SimpleNamespace(
            v1=SimpleNamespace(app_table_record=StubSearchApi())
        )
    )

    result = client.search_by_month("2026年4月", room_name="201")

    conditions = requests[0].request_body.filter.conditions
    assert len(conditions) == 2
    assert conditions[0].field_name == FIELD_MONTH
    assert conditions[1].field_name == FIELD_ROOM_NAME
    assert conditions[1].value == ["201"]
    assert requests[1].page_token == "next-page"
    assert [item[FIELD_ELECTRICITY_PREV] for item in result] == [1452, 1460]
