class State:
    def __init__(self, name):
        self.name = name
        self.start_handler = None
        self.run_handler = None
        self.stop_handler = None

    def set_handlers(self, start=None, run=None, stop=None):
        self.start_handler = start
        self.run_handler = run
        self.stop_handler = stop

    def fire(self, handler):
        handler()

    def stop(self):
        if self.stop_handler is not None:
            self.fire(self.stop_handler)

    def start(self):
        if self.start_handler is not None:
            self.fire(self.start_handler)

    def run(self):
        if self.run_handler is not None:
            self.fire(self.run_handler)


class StateEngine:
    def __init__(self):
        self.states = dict()
        self.current = None
        pass

    def has(self, name):
        return name in self.states

    def add(self, name, start=None, run=None, stop=None):
        if self.has(name):
            print("duplicate state created, ignored: " + name)
            return None
        state = State(name)
        state.set_handlers(start, run, stop)
        self.states[state.name] = state

    def name_of(self, state):
        if state is None:
            return 'No State'
        else:
            return state.name

    def get(self, name):
        if self.has(name):
            return self.states[name]
        else:
            print("has no state called: " + name)
            return None

    def start(self, name):
        old_name = self.name_of(self.current)
        new_state = self.get(name)
        new_name = self.name_of(new_state)
        if old_name == new_name:
            print("State is same as before: " + old_name + ' Ignored state change')
            return
        self.stop()
        self.current = new_state
        if self.current is not None:
            self.current.start()
        print("Changed state from " + old_name + " -> " + new_name)

    def stop(self):
        if self.current is not None:
            self.current.stop()

    def run(self):
        if self.current is not None:
            self.current.run()
