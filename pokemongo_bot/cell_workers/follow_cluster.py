from pokemongo_bot import logger
from pokemongo_bot.step_walker import StepWalker
from pokemongo_bot.cell_workers.utils import distance
from pokemongo_bot.cell_workers.utils import find_biggest_cluster


class FollowCluster(object):
    def __init__(self, bot, config):
        self.bot = bot
        self.is_at_destination = False
        self.announced = False
        self.dest = None
        self.config = config
        self._process_config()

    def _process_config(self):
        self.lured = self.config.get("lured", True)
        self.radius = self.config.get("radius", 50)

    def work(self):
        forts = self.bot.get_forts()
        log_lure_avail_str = ''
        log_lured_str = ''
        if self.lured:
            log_lured_str = 'lured '
            lured_forts = [x for x in forts if 'lure_info' in x]
            if len(lured_forts) > 0:
                self.dest = find_biggest_cluster(self.radius, lured_forts, 'lure_info')
            else:
                log_lure_avail_str = 'No lured pokestops in vicinity. Search for normal ones instead. '
                self.dest = find_biggest_cluster(self.radius, forts)
        else:
            self.dest = find_biggest_cluster(self.radius, forts)

        if self.dest is not None:

            lat = self.dest['latitude']
            lng = self.dest['longitude']
            cnt = self.dest['num_points']

            if not self.is_at_destination:
                msg = log_lure_avail_str + (
                    "Move to destiny {num_points}. {forts} "
                    "pokestops will be in range of {radius}. Walking {distance}m."
                )
                self.bot.event_manager.emit(
                    'found_cluster',
                    sender=self,
                    level='info',
                    formatted=msg,
                    data={
                        'num_points': cnt,
                        'forts': log_lured_str,
                        'radius': str(self.radius),
                        'distance': str(distance(self.bot.position[0], self.bot.position[1], lat, lng))
                    }
                )

                self.announced = False

                if self.bot.config.walk > 0:
                    step_walker = StepWalker(
                        self.bot,
                        self.bot.config.walk,
                        lat,
                        lng
                    )

                    self.is_at_destination = False
                    if step_walker.step():
                        self.is_at_destination = True
                else:
                    self.bot.api.set_position(lat, lng)

            elif not self.announced:
                self.bot.event_manager.emit(
                    'arrived_at_cluster',
                    sender=self,
                    level='info',
                    formatted="Arrived at cluster. {forts} are in a range of {radius}m radius.",
                    data={
                        'forts': str(cnt),
                        'radius': radius
                    }
                )
                self.announced = True
        else:
            lat = self.bot.position[0]
            lng = self.bot.position[1]

        return [lat, lng]
