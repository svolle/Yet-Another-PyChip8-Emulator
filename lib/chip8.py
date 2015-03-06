from array import array
from random import randint
import logging
import sys

HEX_CHARS = [
    0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
    0x20, 0x60, 0x20, 0x20, 0x70,  # 1
    0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
    0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
    0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
    0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
    0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
    0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
    0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
    0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
    0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
    0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
    0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
    0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
    0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
    0xF0, 0x80, 0xF0, 0x80, 0x80   # F
]

DISPLAY_WIDTH = 64
DISPLAY_HEIGHT = 32
HEX_SPRITE_SIZE = 5

CLOCK_FREQUENCY = 1760*1000  # 1.76Mhz, as COSMAC V
TIMERS_UPDATE_FREQUENCY = 60  # 60 Hz


class UnsupportedOpCode(Exception):
    pass


class Processor(object):
    """
    Executes OPCODES in a CHIP-8 VM
    """

    def __init__(self, vm):
        self.vm = vm

    def run(self, opcode):
        """
        Run OPCODE
        """

        nibble = opcode & 0xF000
        self.vm.pc += 2

        if nibble == 0x0:
            if opcode == 0x00E0:
                return self.clear_display()
            if opcode == 0x00EE:
                return self.return_from_subroutine()
            raise UnsupportedOpCode(
                'Unsupported "0x{:X}" opcode received'.format(opcode))

        if nibble in (0x1000, 0xB000):
            return self.jump(opcode)

        if nibble == 0x2000:
            return self.call(opcode)

        if nibble in (0x3000, 0x4000, 0x5000, 0x9000, 0xE000):
            return self.skip(opcode)

        if nibble in (0x6000, 0x7000, 0x8000, 0xA000, 0xC000, 0xF000):
            return self.set_register(opcode)

        if nibble == 0xD000:
            return self.display(opcode)

    def clear_display(self):
        self.vm.logger.debug('CLS')
        self.vm.reset_display()

    def return_from_subroutine(self):
        self.vm.logger.debug('RTN 0x{:X}'.format(self.vm.sp))
        self.vm.sp -= 1
        assert (self.vm.sp >= 0)
        self.vm.pc = self.vm.stack[self.vm.sp]

    def jump(self, opcode):

        jump_addr = None

        # SYS
        if opcode & 0xF000 == 0x1000:
            jump_addr = opcode & 0x0FFF
            assert (jump_addr >= 0x200)

        # JP V0
        elif opcode & 0xF000 == 0xB000:
            jump_addr = (opcode & 0x0FFF) + self.vm.v_registers[0x0]
            assert (jump_addr >= 0x200)
            assert (jump_addr <= 0xFFFF)

        if jump_addr is not None:
            self.vm.logger.debug('JMP 0x{:X}'.format(jump_addr))
            self.vm.pc = jump_addr

    def call(self, opcode):
        subroutine_addr = opcode & 0x0FFF
        self.vm.logger.debug('CALL 0x{:X}'.format(subroutine_addr))

        self.vm.stack[self.vm.sp] = self.vm.pc
        self.vm.sp += 1
        assert (self.vm.sp <= 0xFF)

        self.vm.pc = subroutine_addr

    def skip(self, opcode):
        """
        Instruction skips
        """

        registers = self.vm.v_registers
        logger = self.vm.logger
        x = (opcode & 0x0F00) >> 8
        y = (opcode & 0x00F0) >> 4
        skip = False

        # SE Vx
        if opcode & 0xF000 == 0x3000:
            logger.debug('SE V0x{:X}'.format(x))
            value = opcode & 0x00FF
            if registers[x] == value:
                skip = True

        # SNE Vx
        elif opcode & 0xF000 == 0x4000:
            logger.debug('SNE V0x{:X}'.format(x))
            value = opcode & 0x00FF
            if registers[x] != value:
                skip = True

        # SE Vx,Vy
        elif opcode & 0xF00F == 0x5000:
            logger.debug('SE V0x{:X},V0x{:X}'.format(x, y))
            if registers[x] == registers[y]:
                skip = True

        # SNE Vx,Vy
        elif opcode & 0xF00F == 0x9000:
            logger.debug('SNE V0x{:X},V0x{:X}'.format(x, y))
            if registers[x] != registers[y]:
                skip = True

        # SKP Vx
        elif opcode & 0xF0FF == 0xE09E:
            logger.debug('SKP V0x{:X}'.format(x))
            if self.vm.get_key_state() == registers[x]:
                skip = True

        # SKPN Vx
        elif opcode & 0xF0FF == 0xE0A1:
            logger.debug('SKPN V0x{:X}'.format(x))
            if self.vm.get_key_state() != registers[x]:
                skip = True

        if skip:
            self.vm.pc += 2
            assert (self.vm.pc <= 0xFFFF)

    def set_register(self, opcode):
        """
        Register operations
        """

        vm = self.vm
        logger = self.vm.logger
        registers = self.vm.v_registers
        x = (opcode & 0x0F00) >> 8
        y = (opcode & 0x00F0) >> 4

        # LD Vx
        if opcode & 0xf000 == 0x6000:
            value = opcode & 0x00FF
            logger.debug('LD V0x{:X}, 0x{:X}'.format(x, value))
            registers[x] = value

        # ADD Vx
        elif opcode & 0xF000 == 0x7000:
            value = opcode & 0x00FF
            logger.debug('ADD V0x{:X}, 0x{:X}'.format(x, value))
            registers[x] += value

            if registers[x] > 0xFF:
                registers[x] -= 0xFF + 1

        elif opcode & 0xF000 == 0x8000:

            # VF is reserved
            assert(x < 0xF)
            assert(y < 0xF)

            # LD Vx,Vy
            if opcode & 0xF == 0x0:
                registers[x] = registers[y]
                logger.debug('LD V0x{:X}, V0x{:X}'.format(x, y))

            # OR Vx,Vy
            elif opcode & 0xF == 0x1:
                registers[x] |= registers[y]
                logger.debug('OR V0x{:X}, V0x{:X}'.format(x, y))

            # AND Vx,Vy
            elif opcode & 0xF == 0x2:
                registers[x] &= registers[y]
                logger.debug('AND V0x{:X}, V0x{:X}'.format(x, y))

            # XOR Vx, Vy
            elif opcode & 0xF == 0x3:
                registers[x] ^= registers[y]
                logger.debug('XOR V0x{:X}, V0x{:X}'.format(x, y))

            # ADD Vx, Vy
            elif opcode & 0xF == 0x4:
                registers[x] += registers[y]
                registers[0xF] = int(registers[x] > 0xFF)

                if registers[x] > 0xFF:
                    registers[x] -= 0xFF + 1

                logger.debug('ADD V0x{:X}, V0x{:X}'.format(x, y))

            # SUB Vx, Vy
            elif opcode & 0xF == 0x5:
                registers[0xF] = int(registers[y] > registers[x])
                val_x = registers[x]
                val_x -= registers[y]

                if val_x < 0:
                    val_x += 0xFF + 1
                registers[x] = val_x

                logger.debug('SUB V0x{:X}, V0x{:X}'.format(x, y))

            # SHR Vx {, Vy}
            elif opcode & 0xF == 0x6:
                registers[0xF] = int(registers[x] & 0x1 == 0x1)
                registers[x] >>= 1
                logger.debug('SHR V0x{:X}, V0x{:X}'.format(x, 0xF))

            # SUBN Vx, Vy
            elif opcode & 0xF == 0x7:
                registers[0xF] = int(registers[x] > registers[y])
                val_x = registers[y] - registers[x]

                if val_x < 0:
                    val_x += 0xFF + 1

                registers[x] = val_x
                logger.debug('SUB V0x{:X}, V0x{:X}'.format(x, y))

            # SHL Vx {, Vy}
            elif opcode & 0xF == 0xE:
                registers[0xF] = int(registers[x] & 0x80 == 0x80)
                registers[x] <<= 1
                logger.debug('SHL V0x{:X}, V0x{:X}'.format(x, 0xF))

        # LD I
        elif opcode & 0xF000 == 0xA000:
            value = opcode & 0x0FFF
            vm.i_register = value
            logger.debug('LD I, 0x{:X}'.format(value))

        # RND Vx
        elif opcode & 0xF000 == 0xC000:
            r = randint(0x0, 0xFF)
            registers[x] = r & (opcode & 0x00FF)
            logger.debug('RND V0x{:X}'.format(x))

        # LD Vx, DT
        elif opcode & 0xF0FF == 0xF007:
            registers[x] = vm.dt
            logger.debug('LD V0x{:X}, DT'.format(x))

        # LD Vx, K
        elif opcode & 0xF0FF == 0xF00A:
            def update_register(key):
                nonlocal registers, vm
                registers[x] = key
                vm.is_expecting_key = False
                logger.debug('LD V0x{:X}, K'.format(x))

            vm.is_expecting_key = True
            vm.key_listener = update_register

        # LD DT, Vx
        elif opcode & 0xF0FF == 0xF015:
            vm.dt = registers[x]
            logger.debug('LD DT, V0x{:X}'.format(x))

        # LD ST, Vx
        elif opcode & 0xF0FF == 0xF018:
            vm.st = registers[x]
            logger.debug('LD ST, V0x{:X}'.format(x))

        # ADD I, Vx
        elif opcode & 0xF0FF == 0xF01E:
            vm.i_register += registers[x]
            logger.debug('ADD I, V0x{:X}'.format(x))

        # LD F, Vx
        elif opcode & 0xF0FF == 0xF029:
            vm.i_register = registers[x] * HEX_SPRITE_SIZE
            logger.debug('LD F, V0x{:X}'.format(x))

        # LD B, Vx
        elif opcode & 0xF0FF == 0xF033:
            addr = vm.i_register
            number = registers[x]
            for i in range(addr + 2, addr - 1, -1):
                vm.memory[i] = number % 10
                number //= 10
            logger.debug('LD B, V0x{:X}'.format(x))

        # LD [I], Vx
        elif opcode & 0xF0FF == 0xF055:
            addr = vm.i_register
            for r in range(0, x + 1):
                vm.memory[addr + r] = registers[r]
            logger.debug('LD [I], V0x{:X}'.format(x))

        # LD Vx, [I]
        elif opcode & 0xF0FF == 0xF065:
            addr = vm.i_register
            for r in range(0, x + 1):
                registers[r] = vm.memory[addr + r]
            logger.debug('LD V0x{:X}, [I]'.format(x))

    def display(self, opcode):
        """
        Display operations
        """
        addr = self.vm.i_register
        n = opcode & 0x000F
        x = (opcode & 0x0F00) >> 8
        y = (opcode & 0x00F0) >> 4
        register_x = self.vm.v_registers[x]
        register_y = self.vm.v_registers[y]

        self.vm.logger.debug(
            'DRW A 0x{:X}, N 0x{:X}, X 0x{:X}, Y 0x{:X}'.format(addr, n, x, y))

        self.vm.v_registers[0xF] = 0

        memory = self.vm.memory

        for y in range(0, n):
            sprite = memory[addr + y]
            for x in range(0, 8):
                if sprite & 0x80:
                    collision = self.vm.set_pixel(register_x + x, register_y + y)
                    if collision:
                        self.vm.v_registers[0xF] = 1
                sprite <<= 1


class Chip8(object):
    """
    CHIP-8 VM
    """

    def __init__(self, event_loop, keyboard, renderer):

        # 4kB memory
        self.memory = array('I', (0 for _ in range(0xFFF + 1)))
        # 16-bits stack
        self.stack = array('I', (0 for _ in range(0xF + 1)))

        # 16 x 8-bits registers
        self.v_registers = array('I', (0 for _ in range(0xF + 1)))
        # 16-bits register
        self.i_register = None

        # 16-bits timer
        self.dt = None
        # 16-bits timer
        self.st = None

        # 16-bits program counter
        self.pc = None
        # 8-bits stack pointer
        self.sp = None

        self.display = array('I', [0] * (DISPLAY_WIDTH * DISPLAY_HEIGHT))

        self.processor = Processor(self)
        self.keyboard = keyboard
        self.renderer = renderer
        self.event_loop = event_loop

        self.logger = None
        self.setup_logging()

        self.running = False
        self.display_refresh_needed = False
        self.is_expecting_key = False
        self.key_listener = lambda x: x
        self.delta_t = 0  # Delta T accumulator

        self.reset()

    def setup_logging(self):
        self.logger = logging.getLogger('chip-8')
        self.logger.setLevel('INFO')
        ch = logging.StreamHandler(sys.stdout)
        self.logger.addHandler(ch)

    def set_debug(self, debug):
        if debug:
            debug_level = 'DEBUG'
        else:
            debug_level = 'ERROR'

        self.logger.setLevel(debug_level)

    def reset_display(self):
        for i, _ in enumerate(self.display):
            self.display[i] = 0

        self.display_refresh_needed = True

    def reset(self):
        for i, c in enumerate(HEX_CHARS):
            self.memory[i] = c

        for i in range(len(HEX_CHARS), 0xFFF):
            self.memory[i] = 0

        for i in range(0xF):
            self.stack[i] = 0
            self.v_registers[i] = 0

        self.reset_display()

        self.i_register = 0

        self.dt = 0
        self.st = 0

        self.pc = 0x200
        self.sp = 0

    def load(self, program_file_name):
        addr = 0x200

        self.logger.info('Loading program "{}"'.format(program_file_name))
        with open(program_file_name, 'rb') as program_file:
            while True:
                byte_s = program_file.read(1)
                if not byte_s:
                    break
                self.memory[addr] = byte_s[0]
                addr += 1

    def start(self):
        self.running = True
        self.run_cycle()

    def stop(self):
        self.running = False

    def update_timers(self):
        has_to_decrement = self.delta_t > 1/TIMERS_UPDATE_FREQUENCY
        if has_to_decrement:
            if self.dt > 0:
                self.dt -= 1
            if self.st > 0:
                self.st -= 1
                if self.st <= 0:
                    self.renderer.beep()

            self.delta_t = 0

    def run_cycle(self):
        while self.running:
            if self.is_expecting_key:
                key_state = self.keyboard.get_key_state()
                if key_state is not None:
                    self.key_listener(key_state)

            else:
                opcode = self.memory[self.pc] << 8 | self.memory[self.pc + 1]
                self.logger.debug(
                    'READ OPCODE 0x{:X} AT 0x{:X}'.format(opcode, self.pc))
                self.processor.run(opcode)

                if self.display_refresh_needed:
                    self.refresh_display()

            self.delta_t += self.event_loop.tick() / 1000  # ms -> s
            self.update_timers()

    def set_pixel(self, x, y):
        while x >= DISPLAY_WIDTH:
            x -= DISPLAY_WIDTH
        while x < 0:
            x += DISPLAY_WIDTH

        while y >= DISPLAY_HEIGHT:
            y -= DISPLAY_HEIGHT
        while y < 0:
            y += DISPLAY_HEIGHT

        coord = (y * DISPLAY_WIDTH) + x

        self.display[coord] ^= 1
        self.display_refresh_needed = True

        return not self.display[coord]

    def refresh_display(self):
        self.renderer.refresh(self.display)
        self.display_refresh_needed = False

    def get_key(self):
        return self.keyboard.get_key()

    def get_key_state(self):
        return self.keyboard.get_key_state()