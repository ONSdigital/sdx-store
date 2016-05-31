package com.github.onsdigital.sdxstore.api;

import com.github.davidcarboni.restolino.framework.Api;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.elasticsearch.action.index.IndexResponse;
import org.elasticsearch.client.Client;
import org.elasticsearch.client.transport.TransportClient;
import org.elasticsearch.common.transport.InetSocketTransportAddress;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.ws.rs.POST;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.InetAddress;
import java.net.UnknownHostException;

/**
 * Stores Json.
 */
@Api
public class Store {

    @POST
    public void store(HttpServletRequest request, HttpServletResponse response) throws IOException {
        JsonObject json = new JsonParser().parse(new InputStreamReader(request.getInputStream())).getAsJsonObject();
        try (Client client = getClient()) {
            IndexResponse get = client.prepareIndex("responses", "response")
                    .setSource(json.toString())
                    .get();
        }
    }

    public Client getClient() throws UnknownHostException {
        return TransportClient.builder().build()
                .addTransportAddress(new InetSocketTransportAddress(InetAddress.getByName("192.168.99.100"), 9300));
    }
}
