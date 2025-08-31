package com.bauerfinanz.gutachten.common.openapi;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;

import org.eclipse.microprofile.openapi.OASFactory;
import org.eclipse.microprofile.openapi.OASFilter;
import org.eclipse.microprofile.openapi.models.OpenAPI;
import org.eclipse.microprofile.openapi.models.Operation;
import org.eclipse.microprofile.openapi.models.PathItem.HttpMethod;
import org.eclipse.microprofile.openapi.models.Paths;
import org.eclipse.microprofile.openapi.models.media.Schema;
import org.eclipse.microprofile.openapi.models.tags.Tag;

import io.smallrye.openapi.api.SmallRyeOpenAPI;
import lombok.extern.slf4j.Slf4j;
import software.amazon.awssdk.utils.StringUtils;

/**
 * API OAS Definition will be splitted into public and private oas files.
 * So code generator can use only the pubic one and the privaet one is for docuemntation.
 * The Swagger UI shows all APIs regardless of private/public definition.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
@Slf4j
public class OpenAPIFilter implements OASFilter {

  /**
   * Filter special schema allOf behaviour.
   * Enums with nullable false set allOf.
   * AllOf will be removed and replaced only with reference.
   *
   * @param schema
   *               the schema
   * @return the schema
   */
  @Override
  public Schema filterSchema(final Schema schema) {
    final int allOfIdentifier = 2;
    final List<Schema> allOfList = schema.getAllOf();
    if (allOfList != null && allOfList.size() == allOfIdentifier) {
      // check enum nullable refs
      checkAllOfNullable(schema, allOfList);
      // check binary
      checkAllOfFile(schema, allOfList);

    }
    return OASFilter.super.filterSchema(schema);
  }

  private void checkAllOfFile(final Schema schema, final List<Schema> allOfList) {
    final AtomicReference<Schema> refSchema = new AtomicReference<>();
    final AtomicReference<String> refFile = new AtomicReference<>();
    allOfList.forEach((final Schema s) -> {
      if ("binary".equalsIgnoreCase(s.getFormat()) && StringUtils.isBlank(s.getRef())) {
        refSchema.set(s);
      }
      if (!"binary".equalsIgnoreCase(s.getFormat()) && StringUtils.isNotBlank(s.getRef())) {
        refFile.set(s.getRef());
      }
    });
    if (refSchema.get() != null && StringUtils.isNotBlank(refFile.get())) {
      log.debug("Replace binary allOf - Schema Ref: [{}]", refFile.get());
      schema.setAllOf(null);
      schema.setFormat(refSchema.get().getFormat());
      schema.setDescription(refSchema.get().getDescription());
      schema.setType(refSchema.get().getType());
    }
  }

  private void checkAllOfNullable(final Schema schema, final List<Schema> allOfList) {
    final AtomicBoolean isNotNullable = new AtomicBoolean();
    final AtomicReference<String> ref = new AtomicReference<>();
//    allOfList.forEach((final Schema s) -> {
//      if (s.getNullable() != null && !s.getNullable() && StringUtils.isBlank(s.getRef())) {
//        isNotNullable.set(!s.getNullable());
//      }
//      if (s.getNullable() == null && StringUtils.isNotBlank(s.getRef())) {
//        ref.set(s.getRef());
//      }
//    });
//    if (isNotNullable.get() && StringUtils.isNotBlank(ref.get())) {
//      log.debug("Replace not nullable allOf - Schema Ref: [{}]", ref.get());
//      schema.setAllOf(null);
//      schema.setRef(ref.get());
//    }
  }

  /**
   * Split private and public API definition in separate oas files.
   *
   * @param openAPI
   *                the open API
   */
  @Override
  public void filterOpenAPI(final OpenAPI openAPI) {
    try {
    	
      final OpenAPI publicAPI = OASFactory.createOpenAPI();
      publicAPI.setComponents(openAPI.getComponents());
      publicAPI.setExternalDocs(openAPI.getExternalDocs());
      publicAPI.setExtensions(openAPI.getExtensions());
      publicAPI.setInfo(openAPI.getInfo());
      publicAPI.setOpenapi(openAPI.getOpenapi());
      publicAPI.setSecurity(openAPI.getSecurity());
      publicAPI.setServers(openAPI.getServers());

      final OpenAPI privateAPI = OASFactory.createOpenAPI();
      privateAPI.setComponents(openAPI.getComponents());
      privateAPI.setExternalDocs(openAPI.getExternalDocs());
      privateAPI.setExtensions(openAPI.getExtensions());
      privateAPI.setInfo(openAPI.getInfo());
      privateAPI.setOpenapi(openAPI.getOpenapi());
      privateAPI.setSecurity(openAPI.getSecurity());
      privateAPI.setServers(openAPI.getServers());

      // split Tags
      if (openAPI.getTags() != null) {
        final List<Tag> tagList = new ArrayList<>(openAPI.getTags());
        final Tag privateTag = tagList.stream().filter(t -> "Private".equals(t.getName())).findFirst().orElse(null);
        if (privateTag != null) {
          privateAPI.setTags(List.of(privateTag));
          tagList.remove(privateTag);
        }
        publicAPI.setTags(tagList);
      }

      // split paths
      final Paths paths = openAPI.getPaths();
      final Paths privatePaths = OASFactory.createPaths();
      final Paths publicPaths = OASFactory.createPaths();
      paths.getPathItems().forEach((path, item) -> item.getOperations().forEach((final HttpMethod m, final Operation o) -> {
        if (o.getTags() != null && o.getTags().contains("Private")) {
          privatePaths.addPathItem(path, item);
        } else {
          publicPaths.addPathItem(path, item);
        }
      }));
      publicAPI.setPaths(publicPaths);
      privateAPI.setPaths(privatePaths);

      // write public oas file
      writePublicFiles(publicAPI);

      // write private oas file
      writePrivateFiles(privateAPI);

    } catch (final Exception exc) {
      log.warn("Can't write API Definition file", exc);
    }

  }

  private void writePrivateFiles(final OpenAPI privateAPI) throws IOException {
    final Path privateYamlPath = Path.of("openapi-private.yaml");
    final Path privateJsonPath = Path.of("openapi-private.json");
    if (privateAPI.getPaths().getPathItems() != null && !privateAPI.getPaths().getPathItems().isEmpty()) {
      final String privateYaml = SmallRyeOpenAPI.builder().withInitialModel(privateAPI).build().toYAML();
      Files.writeString(privateYamlPath, privateYaml, StandardCharsets.UTF_8);
      log.debug("Write private API Yaml definition: [{}]", privateYamlPath.toAbsolutePath());

      final String privateJson = SmallRyeOpenAPI.builder().withInitialModel(privateAPI).build().toJSON();
      Files.writeString(privateJsonPath, privateJson, StandardCharsets.UTF_8);
      log.debug("Write private API Json definition: [{}]", privateJsonPath.toAbsolutePath());
    } else {
      // delete existing file
      Files.deleteIfExists(privateYamlPath);
      log.debug("Private API Yaml definition deleted: [{}]", privateYamlPath.toAbsolutePath());

      Files.deleteIfExists(privateJsonPath);
      log.debug("Private API Json definition deleted: [{}]", privateJsonPath.toAbsolutePath());
    }
  }

  private void writePublicFiles(final OpenAPI publicAPI) throws IOException {
    final Path publicYamlPath = Path.of("openapi-public.yaml");
    final Path publicJsonPath = Path.of("openapi-public.json");
    if (publicAPI.getPaths().getPathItems() != null && !publicAPI.getPaths().getPathItems().isEmpty()) {
      final String publicYaml = SmallRyeOpenAPI.builder().withInitialModel(publicAPI).build().toYAML();
      Files.writeString(publicYamlPath, publicYaml, StandardCharsets.UTF_8);
      log.debug("Write public API Yaml definition: [{}]", publicYamlPath.toAbsolutePath());

      final String publicJson = SmallRyeOpenAPI.builder().withInitialModel(publicAPI).build().toJSON();
      Files.writeString(publicJsonPath, publicJson, StandardCharsets.UTF_8);
      log.debug("Write public API Json definition: [{}]", publicJsonPath.toAbsolutePath());
    } else {
      // delete existing file
      Files.deleteIfExists(publicYamlPath);
      log.debug("Public API Yaml definition deleted: [{}]", publicYamlPath.toAbsolutePath());

      Files.deleteIfExists(publicJsonPath);
      log.debug("Public API Json definition deleted: [{}]", publicJsonPath.toAbsolutePath());
    }
  }

}
