import json
from pywikibot.comms.eventstreams import EventStreams

stream = EventStreams(
    streams=["page-create", "revision-create", "recentchange"], since="20260310"
)
stream.register_filter(server_name="en.wikipedia.org", type=("new", "edit"))

while True:
    change: dict = next(stream)
    # print(type(change))
    print(change)
# print(json.dumps(change, indent=4))
# print('{type} on page "{title}" by "{user}" at {meta[dt]}.'.format(**change))
