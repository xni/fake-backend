import time

__author__ = 'stromsund'

import backendconnection


def main():
    uuid = backendconnection.find('summary_hash|nBackTracks=3 summary_hash|nPV=1')
    print 'Created task', uuid
    while True:
        status = backendconnection.check_state([uuid]).get(uuid)
        if status == backendconnection.READY_STATUS:
            break
        print 'Sleeping, because status is:', status
        time.sleep(5)
    print 'Result is:'
    for event in backendconnection.get_search_result(uuid):
        print '   ', event


if __name__ == '__main__':
    main()


