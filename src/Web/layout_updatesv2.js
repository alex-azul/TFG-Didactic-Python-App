let _layout_regular_nodes_data = {};

//Public methods

function layout_bootnode_update_active_regular_nodes(active_regular_node_ip_list) {
    const html_container_id = 'bootnode-regularnode-connections-container';
    _layout_bootnode_update_view(html_container_id, active_regular_node_ip_list);
}

function layout_bootnode_update_active_webapps(active_webapp_ip_list) {
    const html_container_id = 'bootnode-front-connections-container';
    _layout_bootnode_update_view(html_container_id, active_webapp_ip_list);
}

function layout_bootnode_clear_all_ips() {
    const html_regular_node_container_id = 'bootnode-regularnode-connections-container';
    const html_webapp_container_id = 'bootnode-front-connections-container';

    _layout_bootnode_update_view(html_regular_node_container_id, []);
    _layout_bootnode_update_view(html_webapp_container_id, []);
}

function layout_regular_node_update_chain(regular_node_socket_id, regular_node_socket_ip, regular_node_updated_chain) {
    const layout_is_regular_node_data_initialized = _layout_regular_nodes_data[regular_node_socket_id] != undefined;
    if(layout_is_regular_node_data_initialized) {
        _layout_regular_nodes_data[regular_node_socket_id].chain = regular_node_updated_chain;
    }
    else {
        _layout_initialize_regular_node_data(regular_node_socket_id, regular_node_socket_ip, regular_node_updated_chain, []);
    }
    _layout_regular_node_update_view();
}

function layout_regular_node_update_unmined_messages(regular_node_socket_id, regular_node_socket_ip, regular_node_unmined_messages) {
    const layout_is_regular_node_data_initialized = _layout_regular_nodes_data[regular_node_socket_id] != undefined;
    if(layout_is_regular_node_data_initialized) {
        _layout_regular_nodes_data[regular_node_socket_id].unmined_messages = regular_node_unmined_messages;
    }
    else {
        _layout_initialize_regular_node_data(regular_node_socket_id, regular_node_socket_ip, [], regular_node_unmined_messages);
    }
    _layout_regular_node_update_view();
}

function layout_regular_node_clear(regular_node_socket_id) {
    const layout_is_regular_node_data_initialized = _layout_regular_nodes_data[regular_node_socket_id] != undefined;
    if(layout_is_regular_node_data_initialized) {
        delete _layout_regular_nodes_data[regular_node_socket_id];
    }
    _layout_regular_node_update_view();
    _layout_remove_option_from_regular_node_select(regular_node_socket_id);
    _layout_create_messages_from_longest_chain();
}

//Private methods

function _layout_bootnode_update_view(html_container_id, ip_list) {
    const html_container_element = document.getElementById(html_container_id);
    html_container_element.innerHTML = '';

    const is_empty_ip_list = Object.keys(ip_list).length == 0;
    if(!is_empty_ip_list) {
        ip_list.forEach(ip => {
            let new_span = document.createElement('span');
            new_span.innerHTML = ip;
            html_container_element.appendChild(new_span);
        })
    }
}

function _layout_regular_node_update_view() {
    const regular_node_columns_container = document.getElementById('regularnodes-container');
    regular_node_columns_container.innerHTML = '';

    const active_regular_node_socket_ids = Object.keys(_layout_regular_nodes_data);

    active_regular_node_socket_ids.forEach(active_socket_id => {
        const regular_node_data = _layout_regular_nodes_data[active_socket_id];

        const new_column = document.getElementById('column-template').cloneNode(true);
        new_column.id = active_socket_id;
        new_column.getElementsByClassName('bchview-bch-name-label')[0].innerHTML = regular_node_data.ip;
        
        const block_container = new_column.getElementsByClassName('bchview-bch-blocks-container')[0];
        regular_node_data.chain.forEach(block => {
            const new_block = document.getElementById('block-template').cloneNode(true);
            new_block.id = '';

            const block_number_label = new_block.getElementsByClassName('block-attribute-block-number')[0];
            block_number_label.innerHTML = block.block_num;
            block_number_label.title = block.block_num;

            const nonce_label = new_block.getElementsByClassName('block-attribute-nonce')[0];
            nonce_label.innerHTML = block.nonce;
            nonce_label.title = block.nonce;

            const previous_hash_label = new_block.getElementsByClassName('block-attribute-previous-hash')[0];
            previous_hash_label.innerHTML = block.previous_hash;
            previous_hash_label.title = block.previous_hash;

            const hash_label = new_block.getElementsByClassName('block-attribute-hash')[0];
            hash_label.innerHTML = block.hash;
            hash_label.title = block.hash;

            const message_label = new_block.getElementsByClassName('block-attribute-message')[0];
            message_label.innerHTML = block.message.content;
            message_label.title = "Author: " + block.message.author + " Content: " + block.message.content;

            block_container.appendChild(new_block);
        });

        const unmined_messages_container = new_column.getElementsByClassName('bchview-bch-unmined-messages-container')[0];
        regular_node_data.unmined_messages.forEach(unmined_message => {
            const new_unmined_message = document.getElementById('unmined-message-template').cloneNode(true);
            new_unmined_message.id = '';

            const author_label = new_unmined_message.getElementsByClassName('unmined-message-attribute-author')[0];
            author_label.innerHTML = unmined_message.author;
            author_label.title = unmined_message.author;
            
            const message_label = new_unmined_message.getElementsByClassName('unmined-message-attribute-message')[0];
            message_label.innerHTML = unmined_message.content;
            message_label.title = unmined_message.content;

            const date_label = new_unmined_message.getElementsByClassName('unmined-message-attribute-timestamp')[0];
            date_label.innerHTML = unmined_message.timestamp;
            date_label.title = unmined_message.timestamp;

            unmined_messages_container.appendChild(new_unmined_message);
        });

        regular_node_columns_container.appendChild(new_column);

        _layout_create_messages_from_longest_chain();
    });
}

function _layout_create_messages_from_longest_chain() {
    let longest_chain = [];

    const active_regular_node_socket_ids = Object.keys(_layout_regular_nodes_data);

    active_regular_node_socket_ids.forEach(active_socket_id => {
        const chain_to_compare = _layout_regular_nodes_data[active_socket_id].chain;
        longest_chain = chain_to_compare.length > longest_chain.length ? chain_to_compare : longest_chain;
    });

    const comment_section_container = document.getElementById("comment-section-container");
    comment_section_container.innerHTML = "";

    longest_chain.forEach(block => {
        const new_comment = document.getElementById("comment-template").cloneNode(true);
        new_comment.id = "";
    
        const author = block.message.author;
        const content = block.message.content;
        const date = _layout_timestamp_to_date_formatted(block.message.timestamp);

        new_comment.getElementsByClassName("comment-meta")[0].textContent = author + " - " + date;
    
        new_comment.getElementsByClassName("comment-text")[0].textContent = content;
    
        comment_section_container.appendChild(new_comment);
    
        new_comment.scrollIntoView();
    });
}

function _layout_timestamp_to_date_formatted(timestamp) {
    date = new Date(parseInt(timestamp * 1000));
    return date.getDate() + "/" + date.getMonth() + "/" + date.getFullYear() + " " + date.getHours() + ":" + date.getMinutes();
}

function _layout_initialize_regular_node_data(regular_node_socket_id, ip='', chain=[], unmined_messages=[]) {
    _layout_regular_nodes_data[regular_node_socket_id] = {
        'ip':ip,
        'chain':chain,
        'unmined_messages':unmined_messages
    }

    _layout_add_option_to_regular_node_select(regular_node_socket_id, ip);
}

function _layout_add_option_to_regular_node_select(regular_node_socket_id, regular_node_ip) {
    const regular_node_selector = document.getElementById('select-regular-node-select');
    const new_option = document.createElement('option');
    new_option.id = 'regular-node-select-option-' + regular_node_socket_id;
    new_option.value = regular_node_socket_id;
    new_option.innerHTML = regular_node_ip;
    regular_node_selector.appendChild(new_option);
}

function _layout_remove_option_from_regular_node_select(regular_node_socket_id) {
    const regular_node_selector = document.getElementById('select-regular-node-select');
    const regular_node_option = document.getElementById('regular-node-select-option-' + regular_node_socket_id);
    regular_node_selector.removeChild(regular_node_option);
}