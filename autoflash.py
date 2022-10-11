
import getpass
import grp
import json
import os
import pwd
import re
import subprocess

from typing import Sequence, Dict

from impulse import impulse_paths
from impulse.args import args
from impulse.util import buildvars
from impulse.util import resources

from arduino import avrdude


def _get_current_user_groups() -> Sequence[str]:
  user = getpass.getuser()
  for g in grp.getgrall():
    if user in g.gr_mem:
      yield g.gr_name
  yield grp.getgrgid(pwd.getpwnam(user).pw_gid).gr_name


def _prelaunch_checks() -> bool:
  if 'lock' not in _get_current_user_groups():
    print('User needs to be a member of the "lock" group.')
    return False
  return True


def _get_tty_device_drivers() -> Dict[str, str]:
  tty_sys_path = '/sys/class/tty'
  result = {}
  for ttydev in os.listdir(tty_sys_path):
    if 'device' in os.listdir(os.path.join(tty_sys_path, ttydev)):
      result[ttydev] = os.path.realpath(
        os.path.join(tty_sys_path, ttydev, 'device/driver'))
  return result


def _get_arduino_devices() -> Sequence[str]:
  for tty, driver in _get_tty_device_drivers().items():
    if driver.endswith('-uart'):
      yield os.path.join('/dev', tty)


class Device(args.ArgComplete):
  def __init__(self, ttydevice):
    super().__init__(ttydevice)
    self._tty_device = ttydevice
    self._chipset = None
    self._signature = None
    self._board = None

  @classmethod
  def GetBoardMap(cls):
    if hasattr(cls, 'boardmap'):
      return cls.boardmap
    e = avrdude.parse_parts(resources.Resources.Get('arduino/avrdude.conf'))
    cls.boardmap = {x['id']:x for x in e if 'id' in x}
    return cls.boardmap

  @classmethod
  def get_completion_list(cls, stub):
    did_yield = False
    for device in  _get_arduino_devices():
      if device.startswith(stub):
        yield device
        did_yield = True

  def RunCommand(self, command):
    return subprocess.run(command,
                          encoding='utf-8',
                          shell=True,
                          stderr=subprocess.PIPE,
                          stdout=subprocess.PIPE)

  def Construct(self):
    command = '{} -C {} -c arduino -P {} -p {}'.format(
      resources.Resources.Get('bin/avrdude', binary=True),
      resources.Resources.Get('arduino/avrdude.conf'),
      self._tty_device,
      '{}')

    # Guess the chipset first
    r = self.RunCommand(command.format('ATxmega32E5'))
    chipset = re.search(r'\(probably (\S+)\)', r.stderr)
    if not chipset:
      self._chipset = 'unknown'
      return

    conf = Device.GetBoardMap()[chipset.group(1)]
    self._signature = conf['signature']
    self._chipset = conf['id']
    self._board = conf['desc']

  def __str__(self):
    return json.dumps({
      'IO device': self._tty_device,
      'Chipset': self._chipset,
      'Signature': self._signature,
      'Board': self._board
    }, indent=2)

  def __repr__(self):
    return str(self)


command = args.ArgumentParser(complete=True)


@command
def devices():
  """List the devices available"""
  if not _prelaunch_checks():
    return

  devices = [Device(dev) for dev in _get_arduino_devices()]
  completed_count_str = ''

  print('querying [', end='')
  for idx, device in enumerate(devices):
    print('\b'*len(completed_count_str), end='')
    completed_count_str = f'{idx}/{len(devices)}]'
    print(completed_count_str, end='', flush=True)
    device.Construct()

  print('\b'*len(completed_count_str), end='')
  print(f'{len(devices)}/{len(devices)}]')

  chipid = buildvars.Get('chipid')
  for device in devices:
    if device._chipset == chipid:
      print(device)


@command
def flash(device:Device):
  device.Construct()
  chipid = buildvars.Get('chipid')
  if device._chipset != chipid:
    print(f'invalid chipset - expected {chipid}, got {device}')
    exit(1)

  value = device.RunCommand(
    '{} -C {} -p {} -c arduino -P {} -Uflash:w:"{}":i'.format(
      resources.Resources.Get('bin/avrdude', binary=True),
      resources.Resources.Get('arduino/avrdude.conf'),
      chipid, device._tty_device,
      resources.Resources.Get(buildvars.Get('hexfile'))))
  print(value.stderr)
  print(value.stdout)


def main():
  command.eval()