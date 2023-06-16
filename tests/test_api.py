# -*- coding: utf-8 -*-

from acore_db_ssh_tunnel import api


def test():
    _ = api


if __name__ == "__main__":
    from acore_db_ssh_tunnel.tests import run_cov_test

    run_cov_test(__file__, "acore_db_ssh_tunnel.api", preview=False)
