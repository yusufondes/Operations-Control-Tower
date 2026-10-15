"""Private in-process capabilities, never caller-controlled RPC skip flags."""

_ALLOCATION_TOKEN = object()
_EVENT_TOKEN = object()
_DONE_TOKEN = object()
_PREPARATION_TOKEN = object()


def internal_event(env):
    return (
        env.context.get("_oct_campaign_event_token") is _EVENT_TOKEN
        or env.context.get("_oct_campaign_allocation_token") is _ALLOCATION_TOKEN
        or env.context.get("_oct_campaign_done_token") is _DONE_TOKEN
    )
