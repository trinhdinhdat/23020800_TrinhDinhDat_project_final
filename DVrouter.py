from router import Router
from packet import Packet

INFINITY = 9999

class DVrouter(Router):
    def __init__(self, addr, heartbeat_time):
        super().__init__(addr)
        self.heartbeat_time = heartbeat_time
        self.last_time = 0
        self.forwarding_table = {}
        self.distance_vector = {self.addr: (0, self.addr)}  
        self.neighbors = {}  

    def handle_packet(self, port, packet):
        if packet.is_traceroute:
            next_hop = self.forwarding_table.get(packet.dst_addr)
            if next_hop:
                for p, (ep, _) in self.neighbors.items():
                    if ep == next_hop:
                        self.send(p, packet)
                        return
            return  # Không có tuyến, bỏ packet

        updated = False
        received_dv = eval(packet.content)
        sender = packet.src_addr
        endpoint = self.neighbors[port][0]
        cost_to_sender = self.neighbors[port][1]

        for dst, cost in received_dv.items():
            if dst == self.addr:
                continue  # không tự định tuyến về mình

            new_cost = min(INFINITY, cost + cost_to_sender)
            current_cost, current_next_hop = self.distance_vector.get(dst, (INFINITY, None))

            if new_cost < current_cost or (current_next_hop == endpoint and new_cost != current_cost):
                self.distance_vector[dst] = (new_cost, endpoint)
                self.forwarding_table[dst] = endpoint
                updated = True

        if updated:
            self.broadcast_distance_vector()

    def handle_new_link(self, port, endpoint, cost):
        self.neighbors[port] = (endpoint, cost)
        self.distance_vector[endpoint] = (cost, endpoint)
        self.forwarding_table[endpoint] = endpoint
        self.broadcast_distance_vector()

    def handle_remove_link(self, port):
        if port not in self.neighbors:
            return

        endpoint = self.neighbors[port][0]
        del self.neighbors[port]

        updated = False

        # Gỡ bỏ mọi route đi qua endpoint
        to_remove = []
        for dst, (cost, next_hop) in self.distance_vector.items():
            if next_hop == endpoint:
                to_remove.append(dst)

        for dst in to_remove:
            self.distance_vector[dst] = (INFINITY, None)
            self.forwarding_table.pop(dst, None)
            updated = True

        if updated:
            self.broadcast_distance_vector()

    def handle_time(self, time_ms):
        if time_ms - self.last_time >= self.heartbeat_time:
            self.last_time = time_ms
            self.broadcast_distance_vector()

    def broadcast_distance_vector(self):
        for port, (neighbor, _) in self.neighbors.items():
            poisoned_dv = {}
            for dst, (cost, next_hop) in self.distance_vector.items():
                if next_hop == neighbor and dst != neighbor:
                    poisoned_dv[dst] = INFINITY  # poison reverse
                else:
                    poisoned_dv[dst] = cost

            pkt = Packet(Packet.ROUTING, self.addr, neighbor, content=str(poisoned_dv))
            self.send(port, pkt)

    def __repr__(self):
        return f"DVrouter(addr={self.addr})"
