package com.github.onsdigital.sdxstore;

import org.elasticsearch.client.Client;
import org.elasticsearch.client.transport.TransportClient;
import org.elasticsearch.common.settings.Settings;
import org.elasticsearch.common.transport.InetSocketTransportAddress;
import org.elasticsearch.node.Node;

import java.io.File;
import java.net.InetAddress;
import java.net.UnknownHostException;

import static org.elasticsearch.node.NodeBuilder.nodeBuilder;

public class Search {

    private static final String data = "target/es/data";
    private static final String home = "target/es/home";

    //private final Node node;

    public Search() throws UnknownHostException {

        new File(data).mkdirs();
        new File(home).mkdirs();

        // on startup


// on shutdown

        //client.close();


        Settings.builder()
                .put("path.home", home)
                .put("path.data", data)
                .put("http.enabled", "false");

        //node = nodeBuilder()
        //        .local(true)
        //        .node();
    }

    public Client getClient() throws UnknownHostException {
        //return node.client();
        return TransportClient.builder().build()
                .addTransportAddress(new InetSocketTransportAddress(InetAddress.getByName("localhost"), 9300));
    }

    public void shutdown() {
        //node.close();
        //deleteDataDirectory();
    }

    private void deleteDataDirectory() {
        //try {
        //FileUtils.deleteDirectory(new File(dataDirectory));
        //} catch (IOException e) {
        //    throw new RuntimeException("Could not delete data directory of embedded elasticsearch server", e);
        //}
    }

    public static void main(String[] args) throws UnknownHostException {
        new Search().getClient().close();
    }
}