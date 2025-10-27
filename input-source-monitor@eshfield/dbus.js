export const DBUS_INTERFACE = `
    <node>
        <interface name="org.gnome.InputSourceMonitor">
            <signal name="SourceChanged">
                <arg type="s" name="source"/>
            </signal>
        </interface>
    </node>
`;

export const DBUS_PATH = '/org/gnome/InputSourceMonitor';
