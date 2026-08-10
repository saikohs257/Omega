from bentaxis.hashchain import HashChain
from bentaxis.store import BentAxisStore
from runtime.constitutional_record import ConstitutionalRecord
from runtime.events import Event


def test_event_canonicalization_is_order_independent() -> None:
    left = Event.create("sample", {"b": 2, "a": 1}, {"y": "two", "x": "one"})
    right = Event.create("sample", {"a": 1, "b": 2}, {"x": "one", "y": "two"})
    assert left == right


def test_event_is_immutable() -> None:
    event = Event.create("sample", {"value": 1})
    try:
        event.kind = "changed"  # type: ignore[misc]
        raise AssertionError("Event allowed mutation")
    except AttributeError:
        pass


def test_constitutional_record_identity_changes_with_content() -> None:
    base = ConstitutionalRecord(record_type="sample", payload={"value": 1}, timestamp="1")
    changed = ConstitutionalRecord(record_type="sample", payload={"value": 2}, timestamp="1")
    assert base.record_id != changed.record_id


def test_constitutional_record_is_immutable() -> None:
    record = ConstitutionalRecord(record_type="sample", payload={"value": 1}, timestamp="1")
    try:
        record.payload = {}  # type: ignore[misc]
        raise AssertionError("ConstitutionalRecord allowed mutation")
    except AttributeError:
        pass


def test_store_append_order_is_preserved_and_chain_advances() -> None:
    store = BentAxisStore()
    first = Event.create("first", {"n": 1})
    second = Event.create("second", {"n": 2})
    store.append(first)
    head_after_first = store.chain.head
    store.append(second)

    assert [item.event.kind for item in store.events] == ["first", "second"]
    assert store.chain.head != head_after_first
    assert store.snapshot()["count"] == 2
    assert store.snapshot()["digests"] == [item.identity.digest for item in store.events]


def test_hash_chain_is_order_sensitive() -> None:
    first = Event.create("first", {"n": 1})
    second = Event.create("second", {"n": 2})
    forward = HashChain().append_event(first).append_event(second)
    reverse = HashChain().append_event(second).append_event(first)
    assert forward.head != reverse.head


def test_empty_hash_chain_uses_seed_as_head() -> None:
    chain = HashChain(seed="genesis")
    assert chain.head == "genesis"
    assert chain.links == ()
