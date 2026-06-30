from __future__ import annotations


ANY = object()


class Signal:
    def __init__(self, *args, **kwargs) -> None:
        self._receivers = []

    def connect(self, receiver, sender=None, weak=True):  # noqa: ARG002
        self._receivers.append((receiver, sender))
        return receiver

    def disconnect(self, receiver=None, sender=None):  # noqa: ARG002
        if receiver is None and sender is None:
            self._receivers.clear()
            return True
        before = len(self._receivers)
        self._receivers = [item for item in self._receivers if item != (receiver, sender)]
        return len(self._receivers) != before

    def send(self, *args, **kwargs):
        event_sender = args[0] if args else None
        payload_args = args[1:] if args else ()
        results = []
        for receiver, _sender in list(self._receivers):
            if receiver is not None:
                results.append((receiver, receiver(event_sender, *payload_args, **kwargs)))
        return results


class Namespace:
    def signal(self, *args, **kwargs):
        return Signal(*args, **kwargs)
