

# Authors: Veeresh Taranalli <veeresht@gmail.com>
# License: BSD 3-Clause

""" LDPC Codes """
import numpy as np

__all__ = ['get_ldpc_code_params, ldpc_bp_decode']

MAX_POS_LLR = 38.0
MIN_NEG_LLR = -38.0

def get_ldpc_code_params(ldpc_design_filename):
    """
    Extract parameters from LDPC code design file.

    Parameters
    ----------
    ldpc_design_filename : string
        Filename of the LDPC code design file.

    Returns
    -------
    ldpc_code_params : dictionary
        Parameters of the LDPC code.
    """

    ldpc_design_file = open(ldpc_design_filename)

    ldpc_code_params = {}

    [n_vnodes, n_cnodes] = [int(x) for x in ldpc_design_file.readline().split(' ')]
    [max_vnode_deg, max_cnode_deg] = [int(x) for x in ldpc_design_file.readline().split(' ')]
    vnode_deg_list = np.array([int(x) for x in ldpc_design_file.readline().split(' ')[:-1]], np.int32)
    cnode_deg_list = np.array([int(x) for x in ldpc_design_file.readline().split(' ')[:-1]], np.int32)

    cnode_adj_list = -np.ones([n_cnodes, max_cnode_deg], int)
    vnode_adj_list = -np.ones([n_vnodes, max_vnode_deg], int)

    for vnode_idx in xrange(n_vnodes):
        vnode_adj_list[vnode_idx, 0:vnode_deg_list[vnode_idx]] = \
            np.array([int(x)-1 for x in ldpc_design_file.readline().split('\t')])

    for cnode_idx in xrange(n_cnodes):
        cnode_adj_list[cnode_idx, 0:cnode_deg_list[cnode_idx]] = \
            np.array([int(x)-1 for x in ldpc_design_file.readline().split('\t')])

    cnode_vnode_map = -np.ones([n_cnodes, max_cnode_deg], int)
    vnode_cnode_map = -np.ones([n_vnodes, max_vnode_deg], int)
    cnode_list = np.arange(n_cnodes)
    vnode_list = np.arange(n_vnodes)

    for cnode in xrange(n_cnodes):
        for i, vnode in enumerate(cnode_adj_list[cnode, 0:cnode_deg_list[cnode]]):
            cnode_vnode_map[cnode, i] = cnode_list[vnode_adj_list[vnode, :] == cnode]

    for vnode in xrange(n_vnodes):
        for i, cnode in enumerate(vnode_adj_list[vnode, 0:vnode_deg_list[vnode]]):
            vnode_cnode_map[vnode, i] = vnode_list[cnode_adj_list[cnode, :] == vnode]


    cnode_adj_list_1d = cnode_adj_list.flatten().astype(np.int32)
    vnode_adj_list_1d = vnode_adj_list.flatten().astype(np.int32)
    cnode_vnode_map_1d = cnode_vnode_map.flatten().astype(np.int32)
    vnode_cnode_map_1d = vnode_cnode_map.flatten().astype(np.int32)

    pmat = np.zeros([n_cnodes, n_vnodes], int)
    for cnode_idx in xrange(n_cnodes):
        pmat[cnode_idx, cnode_adj_list[cnode_idx, :]] = 1

    ldpc_code_params['n_vnodes'] = n_vnodes
    ldpc_code_params['n_cnodes'] = n_cnodes
    ldpc_code_params['max_cnode_deg'] = max_cnode_deg
    ldpc_code_params['max_vnode_deg'] = max_vnode_deg
    ldpc_code_params['cnode_adj_list'] = cnode_adj_list_1d
    ldpc_code_params['cnode_vnode_map'] = cnode_vnode_map_1d
    ldpc_code_params['vnode_adj_list'] = vnode_adj_list_1d
    ldpc_code_params['vnode_cnode_map'] = vnode_cnode_map_1d
    ldpc_code_params['cnode_deg_list'] = cnode_deg_list
    ldpc_code_params['vnode_deg_list'] = vnode_deg_list

    return ldpc_code_params

def _limit_llr(in_llr):

    out_llr = in_llr

    if in_llr > MAX_POS_LLR:
        out_llr = MAX_POS_LLR

    if in_llr < MIN_NEG_LLR:
        out_llr = MIN_NEG_LLR

    return out_llr


def ldpc_bp_decode(llr_vec, ldpc_code_params, n_iters):
    """
    LDPC Decoder using Belief Propagation (BP).

    Parameters
    ----------
    llr_vec : 1D array of float
        Received codeword LLR values from the channel.

    ldpc_code_params : dictionary
        Parameters of the LDPC code.

    n_iters : int
        Max. number of iterations of decoding to be done.

    Returns
    -------
    dec_word : 1D array of 0's and 1's
        The codeword after decoding.

    out_llrs : 1D array of float
        LLR values corresponding to the decoded output.
    """

    n_cnodes = ldpc_code_params['n_cnodes']
    n_vnodes = ldpc_code_params['n_vnodes']
    max_cnode_deg = ldpc_code_params['max_cnode_deg']
    max_vnode_deg = ldpc_code_params['max_vnode_deg']
    cnode_adj_list = ldpc_code_params['cnode_adj_list']
    cnode_vnode_map = ldpc_code_params['cnode_vnode_map']
    vnode_adj_list = ldpc_code_params['vnode_adj_list']
    vnode_cnode_map = ldpc_code_params['vnode_cnode_map']
    cnode_deg_list = ldpc_code_params['cnode_deg_list']
    vnode_deg_list = ldpc_code_params['vnode_deg_list']

    dec_word = np.zeros(n_vnodes, int)
    out_llrs = np.zeros(n_vnodes, int)

    cnode_msgs = np.zeros(n_cnodes*max_cnode_deg)
    vnode_msgs = np.zeros(n_vnodes*max_vnode_deg)

    # Initialize vnode messages with the LLR values received
    for vnode_idx in xrange(n_vnodes):
        start_idx = vnode_idx*max_vnode_deg
        offset = vnode_deg_list[vnode_idx]
        vnode_msgs[start_idx : start_idx+offset] = llr_vec[vnode_idx]

    # Main loop of Belief Propagation (BP) decoding iterations
    for iter_cnt in xrange(n_iters):

        continue_flag = 0

        # Check Node Update
        for cnode_idx in xrange(n_cnodes):
            #start_idx = cnode_idx*max_cnode_deg
            #offset = cnode_deg_list[cnode_idx]
            #vnode_list = cnode_adj_list[start_idx:start_idx+offset]
            #msg_prod = np.prod(np.tanh(vnode_msgs[vnode_list*max_vnode_deg + cnode_vnode_map[cnode_idx*max_cnode_deg + np.arange(cnode_deg_list[cnode_idx], int)]]/2.0))

            msg_prod = 1.0
            for i in xrange(cnode_deg_list[cnode_idx]):
                vnode = cnode_adj_list[cnode_idx*max_cnode_deg + i]
                msg_prod *= np.tanh(vnode_msgs[vnode*max_vnode_deg +
                                    cnode_vnode_map[cnode_idx*max_cnode_deg + i]]/2.0)

            # Compute messages on outgoing edges using the incoming message product
            for i in xrange(cnode_deg_list[cnode_idx]):
                vnode = cnode_adj_list[cnode_idx*max_cnode_deg + i]
                c_msg = 2.0*np.arctanh(msg_prod/np.tanh(vnode_msgs[vnode*max_vnode_deg +
                                                     cnode_vnode_map[cnode_idx*max_cnode_deg + i]]/2.0))
                cnode_msgs[cnode_idx*max_cnode_deg + i] = c_msg


        # Variable Node Update
        for vnode_idx in xrange(n_vnodes):

            msg_sum = 0
            # Compute sum of all incoming messages at the variable node
            for i in xrange(vnode_deg_list[vnode_idx]):
                cnode = vnode_adj_list[vnode_idx*max_vnode_deg + i]
                msg_sum += cnode_msgs[cnode*max_cnode_deg + vnode_cnode_map[vnode_idx*max_vnode_deg + i]]

            # Compute messages on outgoing edges using the incoming message sum
            for i in xrange(vnode_deg_list[vnode_idx]):
                cnode = vnode_adj_list[vnode_idx*max_vnode_deg + i]
                v_msg = _limit_llr(llr_vec[vnode_idx] + msg_sum - cnode_msgs[cnode*max_cnode_deg + vnode_cnode_map[vnode_idx*max_vnode_deg + i]])
                vnode_msgs[vnode_idx*max_vnode_deg + i] = v_msg

            # Update output LLRs and decoded word
            out_llrs[vnode_idx] = llr_vec[vnode_idx] + msg_sum
            if out_llrs[vnode_idx] > 0:
                dec_word[vnode_idx] = 0
            else:
                dec_word[vnode_idx] = 1

        # Compute if early termination using parity check matrix
        for cnode_idx in xrange(n_cnodes):
            p_sum = 0
            for i in xrange(cnode_deg_list[cnode_idx]):
                p_sum ^= dec_word[cnode_adj_list[cnode_idx*max_cnode_deg + i]]

            if p_sum != 0:
                continue_flag = 1
                break

        # Stop iterations
        if continue_flag == 0:
            break

    return dec_word, out_llrs
