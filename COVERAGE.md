# Coverage definition (v1)

Coverage = packets heard directly by FK50887, identified by raw containing:
  ,qA?,FK50887:

We extract:
- lat/lon (if present)
- rx_db from 'xx.xdB'
- distance to station

We split by tech:
- FLR*/ICA* => FLARM/OGN
- FNT*      => FANET
