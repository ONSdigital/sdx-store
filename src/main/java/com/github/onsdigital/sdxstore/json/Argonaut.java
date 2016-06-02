package com.github.onsdigital.sdxstore.json;

import com.github.davidcarboni.argonaut.Keys;
import com.github.davidcarboni.argonaut.Values;
import com.google.gson.JsonElement;

import java.util.Map;

/**
 * Created by david on 31/05/2016.
 */
public class Argonaut {

    JsonElement json;
    com.github.davidcarboni.argonaut.Keys keys = new Keys();
    Values values = new Values();
    Map<String, Class<? extends JsonElement>> paths;

    public Argonaut(JsonElement json) {
        this.json = json;
        paths = keys.getPaths(json);
    }

    public Class<? extends JsonElement> typeAt(String path) {
        return paths.get(path);
    }

    public JsonElement elementAt(String path) {
        return values.getElement(path, json);
    }

    public String stringAt(String path) {
        return values.getString(path, json);

    }
}
