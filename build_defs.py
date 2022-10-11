
@buildrule
def arduino_shim(target, name, env, **kwargs):
  filepath = os.path.join(target.GetPackageDirectory(), 'shim.py')
  initpath = os.path.join(target.GetPackageDirectory(), '__init__.py')
  target.Execute(f'mkdir -p {target.GetPackageDirectory()}'
                ,f'touch {initpath}'
                ,f'touch {filepath}')
  print(env)
  with open(filepath, 'w') as f:
    f.write('from arduino import autoflash\n')
    f.write('from impulse.util import buildvars\n')
    for e,v in env.items():
      f.write(f'buildvars.Set("{e}", "{v}")\n')
    f.write('def main():\n')
    f.write('  autoflash.main()')
  target.AddFile(initpath)
  target.AddFile(filepath)


@buildrule
def avr_objcopy(target, name, binary, **kwargs):
  target.SetTags('exe')
  target.Execute(f'avr-objcopy -O ihex -R .eeprom bin/{binary} bin/{name}')
  target.AddFile(f'bin/{name}')


@buildmacro
def arduino_installer(macro_env, name, srcs, chipid, cpuid, deps=None, includes=None, **kwargs):
  subtargets = []
  deps = deps or []
  includes = includes or []
  for cc_file in srcs:
    subtarget = cc_file.replace('.', '_') + '_o'
    macro_env.ImitateRule(
      rulefile = '//rules/core/C/build_defs.py',
      rulename = 'cc_compile',
      kwargs = kwargs,
      args = {
        'compiler': 'avr-gcc',
        'name': subtarget,
        'srcs': [ cc_file ],
        'deps': includes,
        'flags': [
          "-mmcu=atmega328p",
          "-DF_CPU=16000000UL",
          "-Os",
        ],
      })
    subtargets.append(f':{subtarget}')

  macro_env.ImitateRule(
    rulefile = '//rules/core/C/build_defs.py',
    rulename = 'cc_combine',
    kwargs = kwargs,
    args = {
      'compiler': 'avr-ld',
      'name': f'{name}_o',
      'deps': subtargets + deps
    })

  macro_env.ImitateRule(
    rulefile = '//rules/core/C/build_defs.py',
    rulename = 'cc_package_binary',
    kwargs = kwargs,
    args = {
      'compiler': 'avr-gcc',
      'name': f'{name}_binary',
      'deps': [f':{name}_o']
    }
  )

  macro_env.ImitateRule(
    rulefile = '//arduino/build_defs.py',
    rulename = 'avr_objcopy',
    kwargs = kwargs,
    args = {
      'name': f'{name}_hex',
      'deps': [f':{name}_binary'],
      'binary': f'{name}_binary',
    }
  )

  macro_env.ImitateRule(
    rulefile = '//arduino/build_defs.py',
    rulename = 'arduino_shim',
    args = {
      'name': f'{name}_shim',
      'env': {
        'chipid': chipid,
        'cpuid': cpuid,
        'hexfile': f'bin/{name}_hex'
      },
    }
  )

  macro_env.ImitateRule(
    rulefile = '//rules/core/Python/build_defs.py',
    rulename = 'py_binary',
    kwargs = kwargs,
    args = {
      'name': f'{name}',
      'srcs': [ 'shim.py' ],
      'deps': [
        '//arduino:autoflash',
        '//impulse/util:buildvars',
        f':{name}_shim'
      ],
      'tools': [
        f':{name}_hex',
        '//arduino:avrdude',
      ],
    }
  )
  
  