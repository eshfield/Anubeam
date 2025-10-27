import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import { Extension } from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Keyboard from 'resource:///org/gnome/shell/ui/status/keyboard.js';

import * as dbus from './dbus.js';

export default class InputSourceMonitorExtension extends Extension {
    constructor(metadata) {
        super(metadata)
        this._dbus = null;
        this._manager = Keyboard.getInputSourceManager();
        this._ownerId = null;
        this._signalId = null;
    }

    enable() {
        this._dbus = Gio.DBusExportedObject.wrapJSObject(dbus.DBUS_INTERFACE, this);
        this._dbus.export(Gio.DBus.session, dbus.DBUS_PATH);

        this._ownerId = Gio.DBus.session.own_name(
            'org.gnome.InputSourceMonitor',
            Gio.BusNameOwnerFlags.NONE,
            null,
            null
        );
        
        this._signalId = this._manager.connect('current-source-changed', () => {
            const source = this._manager.currentSource;
            this._dbus.emit_signal(
                'SourceChanged',
                GLib.Variant.new('(s)', [source.id]),
            );
        });
    }

    disable() {
        if (this._signalId) {
            this._manager.disconnect(this._signalId);
            this._signalId = null;
        }

        if (this._dbus) {
            this._dbus.flush();
            this._dbus.unexport();
            delete this._dbus;
        }
    }
}
