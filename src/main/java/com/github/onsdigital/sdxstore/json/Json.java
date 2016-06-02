package com.github.onsdigital.sdxstore.json;

import com.google.gson.JsonElement;
import com.google.gson.JsonParser;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;

/**
 * Convenience class for parsing Json.
 * Created by david on 29/05/2016.
 */
public class Json {
    public static JsonElement parse(String string) {
        return new JsonParser().parse(string);
    }

    public static JsonElement parse(Reader reader) {
        return new JsonParser().parse(reader);
    }

    public static JsonElement parse(InputStream inputStream) {
        return parse(new InputStreamReader(inputStream));
    }
}
