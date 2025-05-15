from router import Router
from packet import Packet


class DVrouter(Router):
    def __init__(self, addr, heartbeat_time):
        Router.__init__(self, addr)
        self.heartbeat_time = heartbeat_time
        self.last_time = 0
        self.forwarding_table = {}  # dst -> next_hop
        self.distance_vector = {}   # dst -> cost
        self.neighbors = {}  # port -> (endpoint, cost)

    def handle_packet(self, port, packet):
        print(f"[{self.addr}] Received packet on port {port}: {packet.content}")
        if packet.is_traceroute:
            # Forward if known
            next_hop = self.forwarding_table.get(packet.dst_addr)
            if next_hop:
                # Find port for next_hop
                for p, (ep, _) in self.neighbors.items():
                    if ep == next_hop:
                        print(f"[{self.addr}] Forwarding traceroute packet to {next_hop} via port {p}")
                        self.send(p, packet)
                        break
            else:
                print(f"[{self.addr}] No route to {packet.dst_addr}, dropping packet")
        else:
            # Routing packet (distance vector)
            # Parse received distance vector from packet.content (assumed str encoding)
            updated = False
            received_dv = eval(packet.content)  # NOTE: eval for simplicity, be careful
            sender = packet.src_addr
            cost_to_sender = self.neighbors[port][1]

            for dst, cost in received_dv.items():
                new_cost = cost + cost_to_sender
                if dst not in self.distance_vector or new_cost < self.distance_vector[dst]:
                    self.distance_vector[dst] = new_cost
                    self.forwarding_table[dst] = sender
                    updated = True

            if updated:
                print(f"[{self.addr}] Updated distance vector and forwarding table")
                self.broadcast_distance_vector()

    def handle_new_link(self, port, endpoint, cost):
        print(f"[{self.addr}] New link on port {port} to {endpoint} with cost {cost}")
        self.neighbors[port] = (endpoint, cost)
        self.distance_vector[endpoint] = cost
        self.forwarding_table[endpoint] = endpoint
        self.broadcast_distance_vector()

    def handle_remove_link(self, port):
        if port in self.neighbors:
            endpoint = self.neighbors[port][0]
            print(f"[{self.addr}] Removed link on port {port} to {endpoint}")
            del self.neighbors[port]
            if endpoint in self.distance_vector:
                del self.distance_vector[endpoint]
            if endpoint in self.forwarding_table:
                del self.forwarding_table[endpoint]
            self.broadcast_distance_vector()

    def handle_time(self, time_ms):
        if time_ms - self.last_time >= self.heartbeat_time:
            self.last_time = time_ms
            print(f"[{self.addr}] Heartbeat at {time_ms} ms - sending distance vector")
            self.broadcast_distance_vector()
            print(f"[{self.addr}] Current forwarding table: {self.forwarding_table}")

    def broadcast_distance_vector(self):
        dv_str = str(self.distance_vector)
        for port in self.neighbors:
            pkt = Packet(Packet.ROUTING, self.addr, self.neighbors[port][0], content=dv_str)
            print(f"[{self.addr}] Sending distance vector to {self.neighbors[port][0]} on port {port}: {dv_str}")
            self.send(port, pkt)

    def __repr__(self):
        return f"DVrouter(addr={self.addr})"