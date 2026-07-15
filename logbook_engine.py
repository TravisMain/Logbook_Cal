import json
import random
from datetime import date, timedelta, datetime
import math

class LogbookEngine:
    def __init__(self, config):
        self.config = config
        self.start_date = datetime.strptime(config["start_date"], "%Y-%m-%d").date()
        self.end_date = datetime.strptime(config["end_date"], "%Y-%m-%d").date()
        self.opening_odo = config["opening_odo"]
        self.closing_odo = config["closing_odo"]
        self.target_biz_km = config["target_business_km"]
        self.round_only = config.get("round_numbers_only", True)
        self.total_private_km = (self.closing_odo - self.opening_odo) - self.target_biz_km

        # Process holidays
        self.holidays = []
        for h in config.get("holidays", []):
            h_start = datetime.strptime(h["start"], "%Y-%m-%d").date()
            h_end = datetime.strptime(h["end"], "%Y-%m-%d").date()
            self.holidays.append((h_start, h_end, h.get("reason", "")))

        # Process clients
        self.clients = config["clients"]
        self.client_map = {c["name"]: c for c in self.clients}

        self.freq_weights = {
            "Very Frequent": 10,
            "Frequent": 6,
            "Regular": 4,
            "Occasional": 2,
            "Rare": 1
        }

    def is_holiday(self, dt):
        for hs, he, _ in self.holidays:
            if hs <= dt <= he:
                return True
        return False

    def get_available_weekdays(self):
        days = []
        cur = self.start_date
        while cur <= self.end_date:
            if cur.weekday() < 5 and not self.is_holiday(cur):
                days.append(cur)
            cur += timedelta(days=1)
        return days

    def get_available_saturdays(self):
        days = []
        cur = self.start_date
        while cur <= self.end_date:
            if cur.weekday() == 5 and not self.is_holiday(cur):
                days.append(cur)
            cur += timedelta(days=1)
        return days

    def generate_trips(self):
        random.seed(42)

        weekdays = self.get_available_weekdays()
        saturdays = self.get_available_saturdays()

        # 1. Schedule Saturday trips first
        sat_requests = self.config.get("saturdays", [])
        scheduled_sats = []
        sat_pool = list(saturdays)
        random.shuffle(sat_pool)

        for req in sat_requests:
            c_name = req["client"]
            cnt = req["count"]
            for _ in range(cnt):
                if sat_pool:
                    dt = sat_pool.pop()
                    c_info = self.client_map[c_name]
                    dist = round(c_info["one_way_km"]) if self.round_only else c_info["one_way_km"]
                    scheduled_sats.append((dt, [("Home", c_name, dist), (c_name, "Home", dist)]))

        # 2. Determine weekday trips based on average return trip
        avg_dist = sum(c["one_way_km"] * 2 for c in self.clients) / len(self.clients)
        sat_km = sum(sum(l[2] for l in legs) for _, legs in scheduled_sats)
        rem_km = self.target_biz_km - sat_km

        weighted_clients = []
        for c in self.clients:
            w = self.freq_weights.get(c["frequency"], 3)
            weighted_clients.extend([c] * w)

        scheduled_weekdays = []
        current_km = sat_km

        trip_days_pool = list(weekdays)
        trip_days_pool.sort()

        num_trips_needed = max(50, min(len(trip_days_pool) - 10, int(rem_km / max(10, avg_dist * 0.9))))
        step = max(1, len(trip_days_pool) // num_trips_needed)

        selected_days = []
        idx = 0
        while idx < len(trip_days_pool) and len(selected_days) < num_trips_needed:
            jitter = random.choice([0, 0, 1]) if idx + 1 < len(trip_days_pool) else 0
            selected_days.append(trip_days_pool[min(len(trip_days_pool)-1, idx + jitter)])
            idx += step

        for dt in selected_days:
            c = random.choice(weighted_clients)
            dist = round(c["one_way_km"]) if self.round_only else c["one_way_km"]
            scheduled_weekdays.append((dt, [("Work", c["name"], dist), (c["name"], "Work", dist)]))
            current_km += dist * 2

        all_trips = scheduled_sats + scheduled_weekdays
        all_trips.sort(key=lambda x: x[0])

        # 3. Exact Balancing to reach target_biz_km exactly
        total_km = sum(sum(l[2] for l in legs) for _, legs in all_trips)
        diff = round(self.target_biz_km - total_km, 1)

        if self.round_only:
            diff_int = int(round(diff))
            # First, if diff_int is odd, add or subtract 1 from ONE leg of a weekday trip so diff_int becomes even
            if diff_int % 2 != 0:
                for t_idx in range(len(all_trips)):
                    dt, legs = all_trips[t_idx]
                    if legs[0][0] == "Work":
                        c_name = legs[0][1]
                        cur_dist = legs[0][2]
                        if diff_int > 0:
                            # Add 1 km to the outbound leg only
                            all_trips[t_idx] = (dt, [("Work", c_name, cur_dist + 1), (c_name, "Work", cur_dist)])
                            diff_int -= 1
                        else:
                            all_trips[t_idx] = (dt, [("Work", c_name, max(1, cur_dist - 1)), (c_name, "Work", cur_dist)])
                            diff_int += 1
                        break

            # Now diff_int is even, adjust both legs (return trip += 2 or -= 2)
            attempts = 0
            while diff_int != 0 and attempts < 10000:
                attempts += 1
                t_idx = random.randint(0, len(all_trips) - 1)
                dt, legs = all_trips[t_idx]
                if legs[0][0] == "Work":
                    c_name = legs[0][1]
                    cur_one_way = legs[0][2]
                    base_one_way = self.client_map[c_name]["one_way_km"]
                    
                    if diff_int > 0 and cur_one_way < base_one_way + 12:
                        new_one_way = cur_one_way + 1
                        all_trips[t_idx] = (dt, [("Work", c_name, new_one_way), (c_name, "Work", new_one_way)])
                        diff_int -= 2
                    elif diff_int < 0 and cur_one_way > max(3, base_one_way - 12):
                        new_one_way = cur_one_way - 1
                        all_trips[t_idx] = (dt, [("Work", c_name, new_one_way), (c_name, "Work", new_one_way)])
                        diff_int += 2
        else:
            attempts = 0
            while abs(diff) > 1e-5 and attempts < 10000:
                attempts += 1
                t_idx = random.randint(0, len(all_trips) - 1)
                dt, legs = all_trips[t_idx]
                if legs[0][0] == "Work":
                    c_name = legs[0][1]
                    cur_one_way = legs[0][2]
                    delta = round(0.1 if diff > 0 else -0.1, 1)
                    new_one_way = round(cur_one_way + delta, 1)
                    all_trips[t_idx] = (dt, [("Work", c_name, new_one_way), (c_name, "Work", new_one_way)])
                    diff = round(diff - delta * 2, 1)

        # 4. Compute Odometer Ledger
        trip_dates = sorted(set(dt for dt, _ in all_trips))
        gaps = []
        gaps.append((self.start_date, trip_dates[0]))
        for i in range(len(trip_dates) - 1):
            gaps.append((trip_dates[i], trip_dates[i + 1]))
        gaps.append((trip_dates[-1], self.end_date))

        gap_days = [(g[1] - g[0]).days for g in gaps]
        total_gap_days = max(1, sum(gap_days))

        if self.round_only:
            raw_private = [self.total_private_km * gd / total_gap_days for gd in gap_days]
            private_per_gap = [int(round(p)) for p in raw_private]
            err = self.total_private_km - sum(private_per_gap)
            private_per_gap[-1] += err
        else:
            raw_private = [self.total_private_km * gd / total_gap_days for gd in gap_days]
            private_per_gap = [round(p, 1) for p in raw_private]
            err = round(self.total_private_km - sum(private_per_gap), 1)
            private_per_gap[-1] = round(private_per_gap[-1] + err, 1)

        private_before_date = {trip_dates[0]: private_per_gap[0]}
        for i in range(1, len(trip_dates)):
            private_before_date[trip_dates[i]] = private_per_gap[i]

        ledger = []
        cur_odo = self.opening_odo
        last_dt = None

        for trip_date, legs in all_trips:
            if last_dt is None or trip_date != last_dt:
                cur_odo += private_before_date[trip_date]

            for frm, to, dist in legs:
                open_odo = cur_odo
                close_odo = cur_odo + dist
                ledger.append((trip_date, frm, to, open_odo, close_odo, dist))
                cur_odo = close_odo

            last_dt = trip_date

        cur_odo += private_per_gap[-1]
        assert abs(cur_odo - self.closing_odo) < 1e-4, f"Odo mismatch: got {cur_odo}, expected {self.closing_odo}"

        return ledger, all_trips

if __name__ == "__main__":
    print("Logbook Engine loaded.")
