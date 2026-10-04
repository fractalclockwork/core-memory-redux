"""Ngspice 42 + PySpice 1.5 compatibility helpers."""

from __future__ import annotations


def patch_ngspice_stderr_false_positives() -> None:
    """Ignore informational stderr that PySpice 1.5 mis-classifies as fatal.

    Newer ngspice prints lines such as ``Using SPARSE 1.3 as Direct Linear
    Solver`` on stderr; PySpice 1.5 treats any non-``Warning:`` stderr as a
    command failure (PySpice#379).
    """
    from PySpice.Spice.NgSpice.Shared import NgSpiceShared, ffi, ffi_string_utf8

    if getattr(NgSpiceShared, "_cmr_sparse_stderr_patch", False):
        return

    original = NgSpiceShared._send_char

    @staticmethod
    def _send_char(message_c, ngspice_id, user_data):
        self = ffi.from_handle(user_data)
        message = ffi_string_utf8(message_c)
        prefix, _, content = message.partition(" ")
        if prefix == "stderr" and (
            content.startswith("Using ")
            or content.startswith("Note:")
            or "SPARSE" in content
        ):
            self._stdout.append(content)
            return 0
        return original(message_c, ngspice_id, user_data)

    NgSpiceShared._send_char = _send_char
    NgSpiceShared._cmr_sparse_stderr_patch = True
