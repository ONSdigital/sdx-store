package com.github.onsdigital.sdxstore.json;

import com.github.davidcarboni.ResourceUtils;
import com.github.onsdigital.sdxstore.lucene.SdxStore;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import org.junit.Test;

import java.io.IOException;
import java.io.InputStream;

import static org.junit.Assert.*;

/**
 * Test for the {@code Json} class.
 * Created by david on 29/05/2016.
 */
public class JsonTest {

    @Test
    public void shouldParseJsonString() {

        // Given
        String string = "\"test\"";

        // When
        JsonElement json = Json.parse(string);


        // Then
        assertNotNull(json);
        assertTrue(json.isJsonPrimitive());
        assertEquals("test", json.getAsString());
    }

    @Test
    public void shouldParseJsonArray() {

        // Given
        String string = "[\"one\", \"two\", \"three\"]";

        // When
        JsonElement json = Json.parse(string);

        // Then
        assertNotNull(json);
        assertTrue(json.isJsonArray());
        JsonArray array = (JsonArray) json;
        assertEquals(3, array.size());
    }

    @Test
    public void shouldParseJsonObject() {

        // Given
        String string = "{\"one\": \"first\", \"two\": \"second\", \"three\": \"third\"}";

        // When
        JsonElement json = Json.parse(string);

        // Then
        assertNotNull(json);
        assertTrue(json.isJsonObject());
        JsonObject object = (JsonObject) json;
        assertTrue(object.has("one"));
        assertTrue(object.has("two"));
        assertTrue(object.has("three"));
    }

    @Test
    public void shouldParseInputStream() throws IOException {

        // Given
        try (InputStream inputStream = ResourceUtils.getStream("/test.json")) {

            // When
            JsonElement json = Json.parse(inputStream);

            // Then
            assertNotNull(json);
            assertTrue(json.isJsonObject());
            JsonObject object = (JsonObject) json;
            assertTrue(object.has(SdxStore.surveyId));
            assertTrue(object.has(SdxStore.formType));
            assertTrue(object.has(SdxStore.period));
            assertTrue(object.has(SdxStore.ruRef));
        }
    }

}