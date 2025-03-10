# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

# # Double Spend testing
# This test challenge the system with double spends.

import os
from uuid import uuid4
from threading import Thread
import queue

import planetmint_driver.exceptions
from planetmint_driver import Planetmint
from planetmint_driver.crypto import generate_keypair


def test_double_create():
    bdb = Planetmint(os.environ.get("PLANETMINT_ENDPOINT"))
    alice = generate_keypair()

    results = queue.Queue()

    tx = bdb.transactions.fulfill(
        bdb.transactions.prepare(operation="CREATE", signers=alice.public_key, asset={"data": {"uuid": str(uuid4())}}),
        private_keys=alice.private_key,
    )

    def send_and_queue(tx):
        try:
            bdb.transactions.send_commit(tx)
            results.put("OK")
        except planetmint_driver.exceptions.TransportError as e:
            results.put("FAIL")

    t1 = Thread(target=send_and_queue, args=(tx,))
    t2 = Thread(target=send_and_queue, args=(tx,))

    t1.start()
    t2.start()

    results = [results.get(timeout=2), results.get(timeout=2)]

    assert results.count("OK") == 1
    assert results.count("FAIL") == 1
