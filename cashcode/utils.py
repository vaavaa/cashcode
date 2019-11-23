class Bills:
    def __init__(self, bills_dict=dict()):
        self._bills = dict()
        for k in bills_dict:
            if k > 0:
                self._bills[k] = bills_dict[k]

    def __repr__(self):
        ret = ''
        k_list = list(self._bills.keys())
        k_list.sort()
        for k in k_list:
            ret += '\t\t' + str(k) + ': ' + str(self._bills[k]) + '\n'
        return ret

    def __iter__(self):
        return self._bills.__iter__()

    def __getitem__(self, ix):
        if isinstance(ix, tuple):
            raise IndexError('Class %s does not support multiple indexing' % self.__class__.__name__)
        return self._bills[ix]

    def __len__(self):
        return len(self._bills)

    def get(self, k):
        if k in self._bills:
            return self._bills[k]
        else:
            return 0

    @property
    def is_empty(self):
        if not self._bills:
            return True
        return self.total_sum == 0

    @property
    def nominals(self):
        return set(self._bills.keys())

    @property
    def total_sum(self):
        return sum([k*self._bills[k] for k in self._bills])

    sum = total_sum
    total = total_sum

    def add_bills(self, bills):
        for k in bills:
            if k in self._bills:
                self._bills[k] += bills[k]
            else:
                self._bills[k] = bills[k]

    add = add_bills

    def subtract_bills(self, bills):
        '''
        does not subtract and returns False if cannot subtract
        '''
        d = self._bills.copy()
        for k in bills:
            if k in d:
                d[k] -= bills[k]
                if d[k] == 0:
                    d.pop(k)
                elif d[k] < 0:
                    return False
            else:
                return False
        self._bills = d
        return True

    subtract = subtract_bills

    def extract_bills_from_amount(self, amount):
        '''
        returns (<Bill instance>, rest),
        if rest > 0 then bills cannot be extracted from amount given
        '''
        d = self._bills.copy()
        d_list = list(d.keys())
        d_list.sort()
        rest = amount
        for k in d_list[::-1]:
            while d[k]:
                if rest >= k:
                    rest -= k
                    d[k] -= 1
                else:
                    break
        # find the diff and return
        extracted = Bills(self) # copy
        extracted.subtract_bills(d)
        return extracted, rest


class BillChannels:
    def __init__(self, channels_dict):
        self._channels = dict()
        for k in channels_dict:
            if k > 0:
                self._channels[k] = channels_dict[k]

    def __repr__(self):
        ret = ''
        k_list = list(self._channels.keys())
        k_list.sort()
        for k in k_list:
            ret += '\t\t' + str(k) + ': ' + str(self._channels[k]) + '\n'
        return ret

    def __iter__(self):
        return self._channels.__iter__()

    def __getitem__(self, ix):
        if isinstance(ix, tuple):
            raise IndexError('Class %s does not support multiple indexing' % self.__class__.__name__)
        return self._channels[ix]

    def __len__(self):
        return len(self._channels)

    def get(self, k):
        if k in self._channels:
            return self._channels[k]
        else:
            return 0

    def find_optimal_set_of_bills_for_amount(self, amount):
        set_of_nominals = set(self._channels.values())
        list_of_nominals = list(set_of_nominals)
        list_of_nominals.sort()
        bills = dict()
        rest = amount
        for nominal in list_of_nominals[::-1]:
            if nominal > 0:
                while rest - nominal >= 0:
                    rest -= nominal
                    if nominal in bills:
                        bills[nominal] += 1
                    else:
                        bills[nominal] = 1
        return Bills(bills), rest

    def find_channels_in_set_of_bills(self, bills):
        return BillChannels({item[0]:item[1] \
          for item in self._channels.items() \
          if (item[1] in bills) and (bills[item[1]] > 0)})

    def choose_channels_to_accept_amount(self, amount):
        return BillChannels({k: self._channels[k] \
          for k in self._channels \
          if self._channels[k] <= amount})

    @property
    def essp_chan_mask_tuple(self):
        mask = 0
        for k in self._channels:
            mask |= (1 << (k-1))
        mask &= 0xffff
        return ((mask & 0xff), ((mask >> 8) & 0xff))

    @property
    def ccnet_chan_mask_tuple(self):
        mask = 0
        for k in self._channels:
            mask |= (1 << k)
        mask &= 0xffffff
        return (((mask >> 16) & 0xff), ((mask >> 8) & 0xff), (mask & 0xff))

