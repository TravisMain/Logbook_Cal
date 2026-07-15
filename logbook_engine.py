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

        # Select a random 2-week vacation period (14 days) between April 1st and October 1st of the start year
        v_rand = random.Random(self.start_date.year)
        vac_start_offset = v_rand.randint(0, 150)
        self.vac_start = date(self.start_date.year, 4, 1) + timedelta(days=vac_start_offset)
        self.vac_end = self.vac_start + timedelta(days=13)

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
        # Exclude standard annual business shutdown (Dec 15 to Jan 5 inclusive)
        if dt.month == 12 and dt.day >= 15:
            return True
        if dt.month == 1 and dt.day <= 5:
            return True

        # Exclude simulated 2-week vacation period
        if self.vac_start <= dt <= self.vac_end:
            return True

        # Standard South African Public Holidays
        if dt.month == 3 and dt.day == 21: return True  # Human Rights Day
        if dt.month == 4 and dt.day == 27: return True  # Freedom Day
        if dt.month == 5 and dt.day == 1: return True   # Worker's Day
        if dt.month == 6 and dt.day == 16: return True  # Youth Day
        if dt.month == 8 and dt.day == 9: return True   # National Women's Day
        if dt.month == 9 and dt.day == 24: return True  # Heritage Day
        
        # Easter Good Friday & Family Day (2025/2026)
        if dt.year == 2025:
            if dt.month == 4 and (dt.day == 18 or dt.day == 21): return True
        elif dt.year == 2026:
            if dt.month == 4 and (dt.day == 3 or dt.day == 6): return True

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
        
        # Weighted random selection of weekdays (December has weight 0.2, others 1.0)
        def get_day_weight(dt):
            if dt.month == 12:
                return 0.2
            return 1.0

        # Sort using random * (1 / weight) to implement weighted shuffling
        weighted_pool = [(dt, random.random() * (1.0 / get_day_weight(dt))) for dt in trip_days_pool]
        weighted_pool.sort(key=lambda x: x[1])
        shuffled_pool = [x[0] for x in weighted_pool]

        num_trips_needed = max(50, min(len(shuffled_pool) - 10, int(rem_km / max(10, avg_dist * 0.9))))
        selected_days = shuffled_pool[:num_trips_needed]
        unused_days = shuffled_pool[num_trips_needed:]

        def build_trip_py(dt):
            if len(self.clients) >= 2 and random.random() < 0.10:
                c1 = random.choice(self.clients)
                # Find candidates within 15km of c1's distance
                candidates = [c for c in self.clients if c["name"] != c1["name"] and abs(c["one_way_km"] - c1["one_way_km"]) <= 15]
                if candidates:
                    c2 = random.choice(candidates)
                    dist1 = round(c1["one_way_km"]) if self.round_only else c1["one_way_km"]
                    dist2 = round(c2["one_way_km"]) if self.round_only else c2["one_way_km"]
                    transit_dist = round(5 + random.random() * 10) if self.round_only else (5 + random.random() * 10)
                    
                    return (dt, [
                        ("Work", c1["name"], dist1),
                        (c1["name"], c2["name"], transit_dist),
                        (c2["name"], "Work", dist2)
                    ])

            c = random.choice(weighted_clients)
            dist = round(c["one_way_km"]) if self.round_only else c["one_way_km"]
            return (dt, [("Work", c["name"], dist), (c["name"], "Work", dist)])

        all_trips = [build_trip_py(dt) for dt in selected_days]

        # Dynamic trip count adjustment to align close to targetBiz before micro-balancing
        total_km = sum(sum(l[2] for l in legs) for _, legs in all_trips)
        diff = self.target_biz_km - total_km
        adjustment_attempts = 0
        while abs(diff) > 40 and adjustment_attempts < 1000:
            adjustment_attempts += 1
            if diff > 0 and unused_days:
                next_dt = unused_days.pop()
                new_t = build_trip_py(next_dt)
                all_trips.append(new_t)
                diff -= sum(l[2] for l in new_t[1])
            elif diff < 0 and len(all_trips) > 30:
                removed = all_trips.pop()
                unused_days.append(removed[0])
                diff += sum(l[2] for l in removed[1])
            else:
                break

        all_trips.sort(key=lambda x: x[0])

        # 3. Exact Balancing to reach target_biz_km exactly
        total_km = sum(sum(l[2] for l in legs) for _, legs in all_trips)
        diff = round(self.target_biz_km - total_km, 1)

        if self.round_only:
            diff_int = int(round(diff))
            odd_adjusted_idx = -1
            # First, if diff_int is odd, adjust first leg of a simple weekday trip
            if diff_int % 2 != 0:
                for t_idx in range(len(all_trips)):
                    dt, legs = all_trips[t_idx]
                    if len(legs) == 2 and legs[0][0] == "Work":
                        c_name = legs[0][1]
                        cur_dist = legs[0][2]
                        all_trips[t_idx] = (dt, [
                            ("Work", c_name, cur_dist + (1 if diff_int > 0 else -1)),
                            (c_name, "Work", cur_dist)
                        ])
                        diff_int += (-1 if diff_int > 0 else 1)
                        odd_adjusted_idx = t_idx
                        break

            # Now adjust in pairs of 2 km, enforcing STRICT maximum variance of +/- 2 km one-way!
            attempts = 0
            while diff_int != 0 and attempts < 20000:
                attempts += 1
                t_idx = random.randint(0, len(all_trips) - 1)
                if t_idx == odd_adjusted_idx:
                    continue
                dt, legs = all_trips[t_idx]
                if len(legs) == 2 and legs[0][0] == "Work":
                    c_name = legs[0][1]
                    cur = legs[0][2]
                    base = self.client_map[c_name]["one_way_km"]
                    if diff_int > 0 and cur < base + 2:
                        all_trips[t_idx] = (dt, [("Work", c_name, cur + 1), (c_name, "Work", cur + 1)])
                        diff_int -= 2
                    elif diff_int < 0 and cur > max(1, base - 2):
                        all_trips[t_idx] = (dt, [("Work", c_name, cur - 1), (c_name, "Work", cur - 1)])
                        diff_int += 2
                elif len(legs) == 3: # Cluster trip
                    c1_name = legs[0][1]
                    c2_name = legs[2][0]
                    cur1 = legs[0][2]
                    cur2 = legs[2][2]
                    base1 = self.client_map[c1_name]["one_way_km"]
                    base2 = self.client_map[c2_name]["one_way_km"]
                    transit = legs[1][2]
                    if diff_int > 0 and cur1 < base1 + 2:
                        all_trips[t_idx] = (dt, [
                            ("Work", c1_name, cur1 + 1),
                            (c1_name, c2_name, transit),
                            (c2_name, "Work", cur2 + 1)
                        ])
                        diff_int -= 2
                    elif diff_int < 0 and cur1 > max(1, base1 - 2):
                        all_trips[t_idx] = (dt, [
                            ("Work", c1_name, cur1 - 1),
                            (c1_name, c2_name, transit),
                            (c2_name, "Work", cur2 - 1)
                        ])
                        diff_int += 2
        else:
            attempts = 0
            while abs(diff) > 1e-5 and attempts < 20000:
                attempts += 1
                t_idx = random.randint(0, len(all_trips) - 1)
                dt, legs = all_trips[t_idx]
                if len(legs) == 2 and legs[0][0] == "Work":
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
            # Distribute private km with random variance
            private_per_gap = []
            for gd in gap_days:
                base = self.total_private_km * gd / total_gap_days
                factor = 0.4 + random.random() * 1.2
                private_per_gap.append(int(round(base * factor)))
            
            err = self.total_private_km - sum(private_per_gap)
            recon_attempts = 0
            while err != 0 and recon_attempts < 5000:
                recon_attempts += 1
                rand_idx = random.randint(0, len(private_per_gap) - 1)
                if err > 0:
                    private_per_gap[rand_idx] += 1
                    err -= 1
                else:
                    if private_per_gap[rand_idx] > 10:
                        private_per_gap[rand_idx] -= 1
                        err += 1
        else:
            # Decimal distribution with slight random noise
            private_per_gap = []
            for gd in gap_days:
                base = self.total_private_km * gd / total_gap_days
                factor = 0.8 + random.random() * 0.4
                private_per_gap.append(round(base * factor, 1))
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
