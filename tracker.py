import numpy as np
from collections import OrderedDict

class CentroidTracker:
    def __init__(self, max_disappeared=10):
        self.next_id = 0
        self.max_trail = 20000
        self.trail_map = []
        self.object_history = {}
        self.objects = OrderedDict()
        self.disappeared = OrderedDict()
        self.max_disappeared = max_disappeared

    def register(self, centroid):
        self.objects[self.next_id] = centroid
        self.disappeared[self.next_id] = 0
        self.next_id += 1

    def deregister(self, object_id):
        del self.objects[object_id]
        del self.disappeared[object_id]

    def update(self, rects):
        if len(rects) == 0:
            for obj_id in list(self.disappeared.keys()):
                self.disappeared[obj_id] += 1
                if self.disappeared[obj_id] > self.max_disappeared:
                    self.deregister(obj_id)
            return self.objects

        input_centroids = np.array([(int((x1+x2)/2), int((y1+y2)/2)) for x1, y1, x2, y2 in rects])

        if len(self.objects) == 0:
            for i in range(0, len(input_centroids)):
                self.register(input_centroids[i])
        else:
            object_ids = list(self.objects.keys())
            object_centroids = list(self.objects.values())

            D = np.linalg.norm(np.array(object_centroids)[:, None] - input_centroids[None, :], axis=2)
            rows, cols = D.min(axis=1).argsort(), D.argmin(axis=1)[D.min(axis=1).argsort()]
            used_rows, used_cols = set(), set()

            for row, col in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue
                object_id = object_ids[row]
                self.objects[object_id] = input_centroids[col]
                self.disappeared[object_id] = 0
                used_rows.add(row)
                used_cols.add(col)

            unused_rows = set(range(0, D.shape[0])) - used_rows
            unused_cols = set(range(0, D.shape[1])) - used_cols

            for row in unused_rows:
                object_id = object_ids[row]
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)

            for col in unused_cols:
                self.register(input_centroids[col])

            for object_id, centroid in self.objects.items():
                if object_id not in self.object_history:
                    self.object_history[object_id] = []
                self.object_history[object_id].append(centroid)
                self.object_history[object_id] = self.object_history[object_id][-30:]
        
        for c in input_centroids:
            self.trail_map.append(c)
            if len(self.trail_map) > self.max_trail:
                self.trail_map.pop(0)

        return self.objects
