from collections import OrderedDict

# Do I really need to have this as an ordered dictionary?

twitter_actions = OrderedDict([('unique_id', 'text'),
                               ('row_date', 'date'),
                               ('executed', 'numeric'),
                               ('text', 'text'),
                               ('directive', 'text'),
                               ('link', 'text'),
                               ('time_zone', 'numeric'),
                               ('testing', 'numeric'),
                               ('_json', 'text')])

twitter_requests = OrderedDict([('unique_id', 'text'),
                                ('row_date', 'date'),
                                ('responded', 'numeric'),
                                ('text', 'text'),
                                ('link', 'text'),
                                ('testing', 'numeric'),
                                ('_json', 'text')])


