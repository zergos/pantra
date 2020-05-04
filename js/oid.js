let object2id = new WeakMap();
let id2object = new Map();

function set_oid(obj, oid) {
    object2id.set(obj, oid);
    id2object.set(oid, obj);
}

function get_oid(obj) {
    return object2id.get(obj);
}

function get_node(oid) {
    return id2object.get(oid);
}

function delete_id(oid) {
    id2object.delete(oid);
}

