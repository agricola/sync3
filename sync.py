from time import sleep
from typing import List, Callable
from threading import Timer


class Sync:
  def __init__(self, syncers: List[str]):
    self.syncers_names = syncers
    self.syncers_ready = list(map(lambda x: False, syncers))

  def ready(self, syncer: str) -> bool:
    ls = syncer.lower()
    for i, s in enumerate(self.syncers_names):
      if ls == s.lower():
        self.syncers_ready[i] = True
        self.syncers_names[i] = syncer
        return True
    return False

  def check_ready(self) -> bool:
    for s in self.syncers_ready:
      if not s:
        return False
    return True

  def syncers_str(self) -> str:
    return ', '.join(self.syncers_names[:-1]) + " and " + self.syncers_names[-1]


old_syncs = []
current_sync = None
sync_timer = None


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
  if sync_timer != None:
    sync_timer.cancel()
    sync_timer = None


def fail_sync(bot_msg: Callable[[str], None]) -> None:
  end_sync()
  bot_msg("Sync failed!")


def store_old_sync(sync: Sync) -> None:
  old_syncs.append(current_sync)
  if (len(old_syncs) > 10):
    old_syncs.pop(0)


def prepare_syncer_list(starter: str, syncers: List[str]) -> List[str]:
  """ Adds the sync starter to the list, makes all names lowercase,
  and removes duplicates.
  """
  syncers.append(starter)
  l = list(map(lambda x: x.lower(), syncers))
  return list(set(l))

def check_if_valid(syncers: List[str], channel_users: List[str]) -> bool:
  for s in syncers:
    found = False
    for u in channel_users:
      if s == u:
        found = True
        continue
    if not found:
      return False
  return True


#region Public API


def start_sync(starter: str, syncers: List[str], channel_users: List[str],
                bot_msg: Callable[[str], None]) -> None:
  global current_sync, sync_timer
  if current_sync == None:
    if check_if_valid(syncers, channel_users):
      current_sync = Sync(prepare_syncer_list(starter, syncers))
      bot_msg("Buckle up syncers!")
      sync_timer = Timer(120.0, lambda: fail_sync(bot_msg))
      sync_timer.start()
    else:
      bot_msg("Invalid syncer!")
  else:
    bot_msg("Wait for the current sync to finish!")


def ready_syncer(syncer: str, bot_msg: Callable[[str], None]) -> None:
  if current_sync == None:
    bot_msg("There is no sync!")
  else:
    if current_sync.ready(syncer):
      if current_sync.check_ready():
        commence_sync(bot_msg)
    else:
      bot_msg("You are not in the current sync!")


def resync(bot_msg: Callable[[str], None]) -> None:
  if current_sync == None:
    bot_msg("Wait for the current sync to finish!")
  else:
    start_sync(map(lambda x: x[0], old_syncs[-1].syncers))


def desync(bot_msg: Callable[[str], None]) -> None:
  bot_msg("Desyncing...")

#endregion

# temp tests
start_sync('name0', ['name0', 'name1', 'name2'], ['name0', 'name1', 'name2'], print)
ready_syncer('Name4', print)
ready_syncer('name0', print)
ready_syncer('Name1', print)
ready_syncer('Name2', print)
#start_sync('rep', ['name0', 'name1', 'name2'], print)
