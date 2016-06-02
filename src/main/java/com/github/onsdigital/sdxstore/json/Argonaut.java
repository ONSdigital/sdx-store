package com.github.onsdigital.sdxstore.json;

import com.google.gson.JsonElement;
import com.google.gson.JsonParser;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.util.Map;

/**
 * Created by david on 31/05/2016.
 */
public class Argonaut {

    JsonElement json;
    Keys keys = new Keys();
    Values values = new Values();
    Map<String, Class<? extends JsonElement>> paths;

    public static JsonElement parse(String string) {
        return new JsonParser().parse(string);
    }

    public static JsonElement parse(Reader reader) {
        return new JsonParser().parse(reader);
    }

    public static JsonElement parse(InputStream inputStream) {
        return parse(new InputStreamReader(inputStream));
    }


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
