import json
import time
import threading
from DVrouter import DVrouter
from link import Link
from packet import Packet


def run_simulation(config_file):
    with open(config_file) as f:
        config = json.load(f)

    routers = {}
    links = []

    # Create routers
    for r_addr in config['routers']:
        router = DVrouter(r_addr, heartbeat_time=1000)  # heartbeat_time in ms
        routers[r_addr] = router

    # Create links and add to routers
    for (e1, e2, port1, port2, l12, l21) in config['links']:
        link = Link(e1, e2, l12, l21, latency=1)
        links.append(link)
        # Add link to routers if endpoints are routers
        if e1 in routers:
            routers[e1].change_link(("add", port1, e2, link, 1))
        if e2 in routers:
            routers[e2].change_link(("add", port2, e1, link, 1))

    # Start routers in separate threads
    threads = []
    for r in routers.values():
        t = threading.Thread(target=r.run)
        t.daemon = True
        t.start()
        threads.append(t)

    # Run simulation for given end_time seconds
    end_time = config.get('end_time', 10)
    print(f"Running simulation for {end_time} seconds...")
    time.sleep(end_time)

    # Stop routers
    for r in routers.values():
        r.keep_running = False
    for t in threads:
        t.join()


if __name__ == "__main__":
    run_simulation("01_small_net.json")