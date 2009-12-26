#
# Regular cron jobs for the gwrite package
#
0 4	* * *	root	[ -x /usr/bin/gwrite_maintenance ] && /usr/bin/gwrite_maintenance
