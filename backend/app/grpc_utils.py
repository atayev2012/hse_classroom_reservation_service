from __future__ import annotations

from google.protobuf.json_format import MessageToDict


def proto_to_dict(message) -> dict:
    return MessageToDict(
        message,
        preserving_proto_field_name=True,
        always_print_fields_with_no_presence=True,
    )
