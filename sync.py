from time import sleep
from typing import List, Callable
from threading import Timer
from collections import OrderedDict, Counter

FAILED_MSG = "Sync failed!"
NEED_MORE_MSG = "You need more people to sync!"
START_MSG = "Buckle up syncers!"
INVALID_MSG = "Invalid syncer!"
WAIT_MSG = "Wait for the current sync to finish!"
NO_SYNC_MSG = "There is no sync!"
NOT_IN_MSG = "You are not in the current sync!"
NOT_IN_PREV_MSG = "You were not in the last sync!"
DESYNC_MSG = "Desyncing..."
FEW_PPL_GROUP_MSG = "You need more people to make a group!"
NAME_TAKEN_MSG = "There is a already a group with that name!"
GROUP_ADD_MSG = "Group added!"
NOT_IN_GROUP_MSG = "You aren't in that group!"
GROUP_DNE_MSG = "That group does not exist!"

old_syncs = []
current_sync = None
sync_timer = None
sync_groups = OrderedDict()

timer_time = 90.0
group_limit = 100


class SyncGroup:
  def __init__(self, name: str, syncers: List[str]):
    self.name = name
    self.syncers = syncers


class Syncer:
  def __init__(self, name: str):
    self.name = name
    self.ready = False


class Sync:
  def __init__(self, syncers: List[str]):
    self.syncers = [Syncer(s) for s in syncers]

  def ready(self, syncer: str) -> bool:
    ls = syncer.lower()
    for s in self.syncers:
      if ls == s.name.lower():
        s.ready = True
        return True
    return False

  def check_ready(self) -> bool:
    for s in self.syncers:
      if not s.ready:
        return False
    return True

  def syncers_str(self) -> str:
    return name_list_str([s.name for s in self.syncers])

def name_list_str(names) -> str:
    return ', '.join(names[:-1]) + " and " + names[-1]

def commence_sync(bot_msg: Callable[[str], None]) -> None:
  bot_msg("Let's go " + current_sync.syncers_str())
  sleep(2)
  bot_msg("3")
  sleep(2)
  bot_msg("2")
  sleep(2)
  bot_msg("1")
  sleep(2)
  bot_msg("GO!")
  end_sync()


def end_sync() -> None:
  global current_sync, sync_timer
  store_old_sync(current_sync)
  current_sync = None
  if sync_timer is not None:
    sync_timer.cancel()
    sync_timer = None


def fail_sync(bot_msg: Callable[[str], None]) -> None:
  end_sync()
  bot_msg(FAILED_MSG)


def store_old_sync(sync: Sync) -> None:
  old_syncs.append(current_sync)
  if (len(old_syncs) > 10):
    old_syncs.pop(0)


def prepare_syncer_list(starter: str, syncers: List[str]) -> List[str]:
  """ Adds the sync starter to the list, makes all names lowercase,
  and removes duplicates.
  """
  syncers.append(starter)
  return set(map(lambda x: x.lower(), syncers))


def check_if_valid(syncers: List[str], channel_users: List[str]) -> bool:
  for s in syncers:
    found = False
    for u in channel_users:
      if s.lower() == u.lower():
        found = True
        continue
    if not found:
      return False
  return True


#region API


def start_sync(starter: str, syncers: List[str], channel_users: List[str],
               bot_msg: Callable[[str], None]) -> None:
  global current_sync, sync_timer
  if current_sync is None:
    if check_if_valid(syncers, channel_users):
      current_sync = Sync(prepare_syncer_list(starter, syncers))
      if len(current_sync.syncers) <= 1:
        current_sync = None
        bot_msg(NEED_MORE_MSG)
        return
      bot_msg(START_MSG)
      sync_timer = Timer(timer_time, lambda: fail_sync(bot_msg))
      sync_timer.start()
    else:
      bot_msg(INVALID_MSG)
  else:
    bot_msg(WAIT_MSG)


def ready_syncer(syncer: str, bot_msg: Callable[[str], None]) -> None:
  if current_sync is None:
    bot_msg(NO_SYNC_MSG)
  else:
    if current_sync.ready(syncer):
      if current_sync.check_ready():
        commence_sync(bot_msg)
    else:
      bot_msg(NOT_IN_MSG)


def resync(starter: str, channel_users: List[str], bot_msg: Callable[[str], None]) -> None:
  if current_sync is not None:
    bot_msg(WAIT_MSG)
  else:
    syncers = [s.name for s in old_syncs[-1].syncers]
    bot_msg("Resync: " + name_list_str(syncers))
    contains_syncer = False
    for s in syncers:
      if s.lower() == starter.lower():
        contains_syncer = True

    if contains_syncer:
      start_sync(starter, syncers, channel_users, bot_msg)
    else:
      bot_msg(NOT_IN_PREV_MSG)


def desync(caller: str, bot_msg: Callable[[str], None]) -> None:
  if current_sync is None:
    bot_msg(NO_SYNC_MSG)
    return
  if caller in [s.name.lower() for s in current_sync.syncers]:
    bot_msg(DESYNC_MSG)
    end_sync()
  else:
    bot_msg(NOT_IN_MSG)


def create_sync_group(starter: str, name: str, syncers: List[str],
                      channel_users: List[str],
                      bot_msg: Callable[[str], None]) -> None:
  s = prepare_syncer_list(starter, syncers)
  if not check_if_valid(s, channel_users):
    bot_msg(INVALID_MSG)
    return
  if len(s) <= 1:
    bot_msg(FEW_PPL_GROUP_MSG)
    return
  if name.lower() in sync_groups.keys():
    bot_msg(NAME_TAKEN_MSG)
  else:
    sync_groups[name.lower()] = s
    if len(sync_groups) > group_limit:
      r = sync_groups.popitem(False)
      bot_msg("Removing group '%s' because theres too many groups!" % r[0])
    bot_msg(GROUP_ADD_MSG)


def start_sync_by_group(starter: str, group: str, channel_users: List[str],
                        bot_msg: Callable[[str], None]) -> None:
  g = group.lower()
  if g in sync_groups:
    if starter.lower() in sync_groups[g]:
      bot_msg("Group " + g + " sync: " + name_list_str(list(sync_groups[g])))
      start_sync(starter, list(sync_groups[g]), channel_users, bot_msg)
      sync_groups.move_to_end(g)
    else:
      bot_msg(NOT_IN_GROUP_MSG)
  else:
    bot_msg(GROUP_DNE_MSG)


#endregion