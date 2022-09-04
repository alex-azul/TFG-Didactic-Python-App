let _connections_bootnode_socket;
let _connections_regular_node_sockets = {};

//Public methods

function connections_connect_to_bootnode() {
    const valid_ip_regex = /(\d{1,3}\.){3}\d{1,3}:\d+/;
    const bootnode_ip = document.getElementById('bootnode-connect-container-text').value;
    const is_valid_format_ip = valid_ip_regex.test(bootnode_ip);

    const should_create_new_bootnode_socket = !_connections_bootnode_socket || _connections_bootnode_socket.disconnected;

    if(is_valid_format_ip && should_create_new_bootnode_socket) {
        try{
            _connections_bootnode_socket_factory(bootnode_ip);
        }
        catch(error)
        {
            console.log(error);
        }
    }
}

function connections_selected_regular_node_mine() {
    const regular_node_select = document.getElementById('select-regular-node-select');
    const regular_node_socket_id = regular_node_select.options[regular_node_select.selectedIndex].value;
    _connections_emit_from_regular_node_socket(regular_node_socket_id, 'mine');
}

function connections_selected_regular_node_mine_locally() {
    const regular_node_select = document.getElementById('select-regular-node-select');
    const regular_node_socket_id = regular_node_select.options[regular_node_select.selectedIndex].value;
    _connections_emit_from_regular_node_socket(regular_node_socket_id, 'mine-locally');
}

function connections_selected_regular_node_consensus() {
    const regular_node_select = document.getElementById('select-regular-node-select');
    const regular_node_socket_id = regular_node_select.options[regular_node_select.selectedIndex].value;
    _connections_emit_from_regular_node_socket(regular_node_socket_id, 'consensus');
}

function connections_selected_regular_node_new_unmined_message() {
    const regular_node_select = document.getElementById('select-regular-node-select');
    const regular_node_socket_id = regular_node_select.options[regular_node_select.selectedIndex].value;
    const messageAuthorTextbox = document.getElementById("app-send-comment-author-textbox");
    const messageTextTextbox = document.getElementById("app-send-comment-message-textbox");

    const author = messageAuthorTextbox.value == "" ? "Anonimo" : messageAuthorTextbox.value;
    const text = messageTextTextbox.value;
    messageTextTextbox.value = "";

    const data = {
        "author": author,
        "content": text
    }

    _connections_emit_from_regular_node_socket(regular_node_socket_id, 'new_unmined_message', data);
}

//Private methods

function _connections_generate_regular_node_sockets_from_ip_list(updated_active_regular_node_ip_list) {
    const current_active_regular_node_ip_list = Object.values(_connections_regular_node_sockets).map(socket_info => {return socket_info.ip;});

    const new_regular_node_ip_list = updated_active_regular_node_ip_list.filter(x => !current_active_regular_node_ip_list.includes(x));

    new_regular_node_ip_list.forEach(regular_node_ip => {
        try{
            _connections_regular_node_socket_factory(regular_node_ip);
        }
        catch(error) {
            console.log(error);
        }
    });
}

function _connections_bootnode_socket_factory(bootnode_ip) {
    const socket_options = {"reconnectionAttempts":3};
    const socket = io(bootnode_ip, socket_options);

    socket.on('connect', function() {
        _connections_bootnode_socket = socket;

        socket.on('updated_active_regular_nodes_list', function(received_data) {
            layout_bootnode_update_active_regular_nodes(received_data.active_regular_node_ip_list);
            _connections_generate_regular_node_sockets_from_ip_list(received_data.active_regular_node_ip_list);
        });
    
        socket.on('updated_active_webapps_list', function(received_data) {
            layout_bootnode_update_active_webapps(received_data.active_webapp_ip_list);
        })
    
        socket.on('disconnect', function() {
            _connections_bootnode_socket = null;
            layout_bootnode_clear_all_ips();
        });
    });
}

function _connections_regular_node_socket_factory(regular_node_ip) {
    const socket_options = {"reconnectionAttempts":3};
    const socket = io(regular_node_ip, socket_options);

    socket.on('connect', function() {
        const socket_id = socket.id;

        _connections_regular_node_sockets[socket_id] = {"ip": regular_node_ip, "socket": socket};

        socket.on('updated_chain', function(received_data) {
            regular_node_chain = received_data.chain;
            layout_regular_node_update_chain(socket_id, regular_node_ip, regular_node_chain);
        });
    
        socket.on('updated_unmined_messages', function(received_data) {
            regular_node_unmined_messages = received_data.unmined_messages;
            layout_regular_node_update_unmined_messages(socket_id, regular_node_ip, regular_node_unmined_messages);
        });

        socket.on('disconnect', function() {
            delete _connections_regular_node_sockets[socket_id];
            layout_regular_node_clear(socket_id);
        });

        _connections_emit_from_regular_node_socket(socket_id, 'initialized');
    });
}

function _connections_emit_from_regular_node_socket(regular_node_socket_id, event, data) {
    const socket = _connections_regular_node_sockets[regular_node_socket_id].socket;
    const socket_exists = socket != undefined;

    if(socket_exists) {
        if(data) {
            socket.emit(event, data);
        }
        else {
            socket.emit(event);
        }
    }
}