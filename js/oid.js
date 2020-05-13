let OID = {
    object2id: new WeakMap(),
    id2object: new Map(),
    set: function(obj, oid) {
        //obj.id = oid;
        OID.object2id.set(obj, oid);
        OID.id2object.set(oid, obj);
    },
    get: function (obj) {
        //return parseInt(obj.id);
        return OID.object2id.get(obj);
    },
    node: function(oid) {
        //return document.getElementById(oid);
        return OID.id2object.get(oid);
    },
    delete: function(oid) {
        OID.id2object.delete(oid);
    },
    clear: function () {
        OID.id2object.clear();
    }
};
