from collections import Counter

def compare_clocks(view_list, meta_data, local_clock, sender_socket):
    # If the sender is the client then return true so that it still delivers
    if sender_socket not in view_list or meta_data == "":
        return True
    if meta_data[sender_socket] - 1 == local_clock[sender_socket]:
        for process in local_clock:
            if process == sender_socket:
                continue
            elif not meta_data[process] <= local_clock[process]:
                return False
        return True

    else:
        return False