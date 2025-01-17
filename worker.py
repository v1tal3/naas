#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
 worker.py
 Author: Brett Lykins (lykinsbd@gmail.com)
 Description: Handle launching of rq workers
"""

from argparse import ArgumentParser, Namespace
from logging import basicConfig, getLogger
from naas.library.netmiko_lib import netmiko_send_command, netmiko_send_config  # noqa F401
from redis import Redis
from rq import Connection, Worker, Queue
from multiprocessing import Process
from socket import gethostname
from time import sleep
from typing import Optional, Sequence


logger = getLogger("rq_worker_init")


def main() -> None:
    """
    Launch rq workers, default of 50
    :return:
    """

    # Parse some args
    args = arg_parsing()

    # Setup logging
    basicConfig(level=args.log_level)

    # Sleep 10 seconds to allow Redis to come up
    logger.debug("Sleeping %s seconds to allow Redis to initialize.", args.sleep)
    sleep(args.sleep)

    # Launch the workers
    logger.debug("Creating %s workers", args.workers)
    processes = []
    hostname = gethostname()
    for w in range(1, args.workers + 1):
        proc = Process(
            target=worker_launch,
            kwargs={
                "name": f"naas_{hostname}_{w}",
                "queues": args.queues,
                "redis_host": args.redis,
                "redis_port": args.port,
                "redis_pw": args.auth_password,
                "log_level": args.log_level,
            },
        )
        processes.append(proc)
        proc.start()


def arg_parsing() -> Namespace:
    """
    Parse the CLI arguments and return them in an Argparse Namespace
    :return:
    """

    argparser = ArgumentParser(description="RQ Multi-worker Launcher")
    argparser.add_argument(
        "workers", type=int, nargs="?", default=100, help="The number of workers to launch. Default: 100"
    )
    argparser.add_argument(
        "-q",
        "--queues",
        type=str,
        nargs="+",
        default="naas",
        help="What queue(s) are we are working out of?  Default: naas",
    )
    argparser.add_argument(
        "-r", "--redis", type=str, default="redis", help="What Redis server are we using? Defualt: redis"
    )
    argparser.add_argument(
        "-p", "--port", type=int, default=6379, help="What port is the Redis server listening on? Default: 6379"
    )
    argparser.add_argument(
        "-a", "--auth_password", type=str, help="Password if the Redis server requires authentication."
    )
    argparser.add_argument(
        "-s",
        "--sleep",
        type=int,
        default=10,
        nargs="?",
        help="How many seconds to sleep to give Redis a chance to initialize. Default: 10",
    )
    argparser.add_argument(
        "-l",
        "--log_level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="What log-level are we to log at",
    )

    return argparser.parse_args()


def worker_launch(
    name: str, queues: Sequence[Queue], redis_host: str, redis_port: int, log_level: str, redis_pw: Optional[str] = None
) -> None:
    """
    Function for launching an rq worker
    :param name:
    :param queues:
    :param redis_host:
    :param redis_port:
    :param redis_pw:
    :param log_level:
    :return:
    """

    # Initialize our Redis connection
    logger.debug("Initializing Redis connection to redis://%s:%s", redis_host, str(redis_port))
    redis_conn_dict = {"host": redis_host, "port": redis_port}
    if redis_pw:
        redis_conn_dict["password"] = redis_pw
    with Connection(connection=Redis(**redis_conn_dict)) as redis_conn:

        logger.debug(
            "Starting rq worker %s, with connection to redis://%s:%s, to watch the following queue(s): %s",
            name,
            redis_host,
            redis_port,
            queues,
        )
        w = Worker(queues=queues, name=name, connection=redis_conn)
        w.work(logging_level=log_level)


if __name__ == "__main__":
    main()
