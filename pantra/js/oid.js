let OID = {
    object2id: new WeakMap(),
    id2object: new Map(),
    set: function(obj, oid) {
        //obj.id = oid;
        this.object2id.set(obj, oid);
        this.id2object.set(oid, obj);
    },
    get: function (obj) {
        //return parseInt(obj.id);
        return this.object2id.get(obj);
    },
    node: function(oid) {
        //return document.getElementById(oid);
        return this.id2object.get(oid);
    },
    delete: function(oid) {
        this.id2object.delete(oid);
        SCRIPTS.delref(oid);
    },
    clear: function () {
        this.id2object.clear();
        SCRIPTS.clear();
    }
};

let SCRIPTS = {
    uid2script: new Map(),
    oid2uid: new Map(),
    uid2oids: new Map(),
    new: function (script, uid) {
        this.uid2script.set(uid, script);
        this.uid2oids.set(uid, []);
    },
    exists: function (uid) {
        return !!this.uid2script.get(uid);
    },
    addref: function (uid, oid) {
        let oids = this.uid2oids.get(uid);
        oids.push(oid);
        this.uid2oids.set(uid, oids);
        this.oid2uid.set(oid, uid);
    },
    delref: function (oid) {
        let uid = this.oid2uid.get(oid);
        if (!uid) return;
        this.oid2uid.delete(oid);
        let oids = this.uid2oids.get(uid);
        oids.splice(oids.indexOf(oid), 1);
        if (oids.length === 0) {
            this.uid2oids.delete(uid);
            let elem = this.uid2script(uid);
            elem.remove();
            this.uid2script.delete(uid);
        }
    },
    clear: function () {
        for (let script of this.uid2script.values()) {
            script.remove();
        }
        this.uid2script.clear();
        this.oid2uid.clear();
        this.uid2oids.clear();
    }
};