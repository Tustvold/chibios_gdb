class ChibiosPrefixCommand(gdb.Command):
    "Prefix for ChibiOS related helper commands"

    def __init__(self):
        super(ChibiosPrefixCommand, self).__init__("chibios",
                                                   gdb.COMMAND_SUPPORT,
                                                   gdb.COMPLETE_NONE,
                                                   True)

class ChibiosThread(object):
    """ Class to model ChibiOS/RT thread"""

    def __init__(self, thread):
        self._stklimit = 0
        self._r13 = 0
        self._address = 0
        self._stack_size = 0
        self._stack_unused = 0
        self._name = "<no name>"
        self._state = 0
        self._flags = 0
        self._prio = 0
        self._refs = 0
        self._time = 0

        # Extract all thread information
        # Get a gdb.Type which is a void pointer. 
        void_p = gdb.lookup_type('void').pointer()

        # stklimit and r13 are different pointer types, so cast to get the arithmetic correct
        self._stklimit = thread['p_stklimit'].cast(void_p)
        self._r13 = thread['p_ctx']['r13'].cast(void_p)
        self._stack_size = self._r13 - self._stklimit
        self._address = thread.address
        
        # Try to dump the entire stack of the thread
        inf = gdb.selected_inferior()
            
        try:
            stack = inf.read_memory(self._stklimit, self._stack_size)
        except gdb.MemoryError as e:
            print e
            raise gdb.GdbError('Stack pointer invalid?')

        # Find the first non-'U' (0x55) element in the stack space. 
        for i, each in enumerate(stack):
            if (each != 'U'):
                break;

        self._stack_unused = i
    
        if len(thread['p_name'].string()) > 0:
            self._name = thread['p_name'].string()

        self._state = thread['p_state']
        self._flags = thread['p_flags']
        self._prio = thread['p_prio']
        self._refs = thread['p_refs']
        self._time = thread['p_time']

    @property
    def name(self):
        return self._name

    @property
    def stack_size(self):
        return self._stack_size

    @property
    def stack_limit(self):
        return self._stklimit

    @property
    def stack_start(self):
        return self._r13

    @property
    def stack_unused(self):
        return self._stack_unused

    @property
    def address(self):
        return self._address

    @property
    def state(self):
        return self._state

    @property
    def flags(self):
        return self._flags

    @property
    def prio(self):
        return self._prio

    @property
    def time(self):
        return self._time




class ChibiosThreadsCommand(gdb.Command):
    """Print all the ChibiOS threads and their stack usage.

    This will not work if ChibiOS was not compiled with... """
    
    def __init__(self):
        super(ChibiosThreadsCommand, self).__init__("chibios threads",
                                                    gdb.COMMAND_SUPPORT,
                                                    gdb.COMPLETE_NONE)

    def invoke(self, args, from_tty):
        thread_type = gdb.lookup_type('Thread')
        rlist_p = gdb.parse_and_eval('&rlist')
        rlist_as_thread = rlist_p.cast(thread_type.pointer())
        newer = rlist_as_thread.dereference()['p_newer']
        older = rlist_as_thread.dereference()['p_older']

        print "%-10s %-10s %-10s %6s/%6s  %s" % ("Address", "StkLimit", "Stack", "Free", "Total", "Name")
        while (newer != rlist_as_thread):

            ch_thread = ChibiosThread(newer.dereference())
            print "0x%x 0x%x 0x%x %6d/%6d  %s" % (ch_thread.address,
                                                  ch_thread.stack_limit,
                                                  ch_thread.stack_start,
                                                  ch_thread.stack_unused,
                                                  ch_thread.stack_size,
                                                  ch_thread.name)

            current = newer
            newer = newer.dereference()['p_newer']
            older = newer.dereference()['p_older']

            if (older != current):
                raise gdb.GdbError('Rlist pointer invalid--corrupt list?')


class ChibiosThreadCommand(gdb.Command):
    """Print information about the currently selected thread"""

    def __init__(self):
        super(ChibiosThreadCommand, self).__init__("chibios thread",
                                                    gdb.COMMAND_SUPPORT,
                                                    gdb.COMPLETE_NONE)
    def invoke(self, args, from_tty):
        thread = gdb.selected_thread();
        if thread is not None:
            # inf.ptid is PID, LWID, TID; TID corresponds to the address in
            # memory of the Thread*.
            newer = thread.ptid[2]
            print "%-10s %-10s %-10s %6s/%6s  %s" % ("Address", "StkLimit", "Stack", "Free", "Total", "Name")

            thread_struct = gdb.parse_and_eval('(Thread *)%d' % (newer)).dereference()
            print chibios_extract_thread(thread_struct)

        else:
            print "No threads found--run info threads first"
            

# class ChibiosTraceCommand(gdb.Command):
#     """ Print the last entries in the trace buffer"""

#     def __init__(self):
#         super(ChibiosTraceCommand, self).__init__("chibios trace",
#                                                   gdb.COMMAND_SUPPORT,
#                                                   gdb.COMPLETE_NONE)

#     def invoke(self, args, from_tty):
#         count = 10
#         if args is not None:
#             count = int(args[0])

#         trace_max = gdb.parse_and_eval(
        

            
ChibiosPrefixCommand()
ChibiosThreadsCommand()
ChibiosThreadCommand()
