def parse_log_file(df,g,file_names,file_type):
    """

    Arguments:
    file_type: int, 1 for batch_log_file
                    2 for stream_log_file
    """
    import numpy as np
    import pandas as pd
    from ast import literal_eval  
    from purchase_statistics import get_purchase_statistics
    from json import dumps
 
    if ( (file_type != 1) & ( file_type != 2 ) ):
        print("Error found in parse_log_file, file_type should be 1 or 2")
        exit(1)

    # Read input files:
    if ( file_type == 1 ):
        input_file = file_names['batch_log']
    elif ( file_type == 2 ):
        input_file = file_names['stream_log']
        output_file = file_names['flagged_purchases']
        f_out = open(output_file,"w")
    f_in = open(input_file,"r")

    if ( file_type == 1 ):
        # Read first line of the file, and store "D", "T" values:
        line = f_in.readline()
        # Use literal_eval to convert string to dictionary,
        # This is safer than using eval. As its own docs say:
        # help(ast.literal_eval)
        # Help on function literal_eval in module ast:
        #     literal_eval(node_or_string)
        #     Safely evaluate an expression node or a string containing a Python
        #     expression.  The string or node provided may only consist of the following
        #     Python literal structures: strings, numbers, tuples, lists, dicts, booleans, and None.
        dic=literal_eval(line)
        g.network_degree=int(dic['D'])
        g.tracked_number_of_purchases=int(dic['T'])

    # Read rest of the file and construct network
    purchase_index=0
    for line in f_in.readlines():
        try:
            dic=literal_eval(line)
        except:
            continue
        event_type=dic['event_type']
        timestamp=dic['timestamp']
        if ( event_type == 'befriend' ):
            id1=str(dic['id1'])
            id2=str(dic['id2'])
            g.add_friend(id1,id2)
            g.update_friend_list()
            #g.show_social_networks()
        elif( event_type == 'unfriend' ):
            id1=str(dic['id1'])
            id2=str(dic['id2'])
            g.del_friend(id1,id2)
            g.update_friend_list()
            #g.show_social_networks()
        elif ( event_type == 'purchase' ):
            purchase_index=purchase_index+1
            uid=str(dic['id'])
            amount=np.float(dic['amount'])
            # Add new row to dataset:
            #newrow=[timestamp,purchase_index,uid,amount]
            newrow=[timestamp,uid,amount]
            df.loc[len(df.values)]=newrow
            # Sort by timestamp in descending order, and then by index in ascending order.
            df=df.sort_values(by='timestamp',ascending=False)
            # If user is not in network, add it:
            g.if_notpresent_add_user(uid)
            # Update purchase statistics:
            if ( file_type == 2 ):
                purchase={"id": uid, "amount": amount}
                purchase_stats=get_purchase_statistics(purchase,g,df)
                if ( purchase_stats['anomalous'] ):
                    flagged_purchase={"event_type": "purchase",
                    "timestamp": timestamp,
                    "id": uid,
                    "amount": str(amount),
                    "mean": purchase_stats['mean'],
                    "sd": purchase_stats['sd']}
                    f_out.write(dumps(flagged_purchase))
                    #
    #g.show_social_networks()
    f_in.close()
    if ( file_type == 2 ):
        f_out.close()
    return df