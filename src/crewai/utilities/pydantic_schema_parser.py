from typing import Type, get_args, get_origin, List, Union
from pydantic import BaseModel


class PydanticSchemaParser(BaseModel):
    model: Type[BaseModel]

    def get_schema(self) -> str:
        """
        Public method to get the schema of a Pydantic model.

        :param model: The Pydantic model class to generate schema for.
        :return: String representation of the model schema.
        """
        return self._get_model_schema(self.model)

    def _get_model_schema(self, model: Type[BaseModel], depth: int = 0) -> str:
        indent = " " * 4 * depth
        lines = [
            f"{indent}- {field_name}: {self._get_field_type(field, depth + 1)}"
            for field_name, field in model.model_fields.items()
        ]
        return "\n".join(lines)

    def _get_field_type(self, field, depth: int) -> str:
        field_type = field.annotation
        origin = get_origin(field_type)

        if origin in {list, List}:
            list_item_type = get_args(field_type)[0]
            return self._format_list_type(list_item_type, depth)

        if origin is Union:
            return self._format_union_type(field_type, depth)

        if isinstance(field_type, type) and issubclass(field_type, BaseModel):
            nested_schema = self._get_model_schema(field_type, depth)
            nested_indent = " " * 4 * (depth - 1)
            return f"{field_type.__name__}[\n{nested_schema}\n{nested_indent}]"

        return field_type.__name__

    def _format_list_type(self, list_item_type, depth: int) -> str:
        if isinstance(list_item_type, type) and issubclass(list_item_type, BaseModel):
            nested_schema = self._get_model_schema(list_item_type, depth + 1)
            nested_indent = " " * 4 * (depth - 1)
            return f"List[\n{nested_schema}\n{nested_indent}]"
        return f"List[{list_item_type.__name__}]"

    def _format_union_type(self, field_type, depth: int) -> str:
        args = get_args(field_type)
        non_none_type = next(arg for arg in args if arg is not type(None))
        return f"Optional[{self._get_field_type_for_annotation(non_none_type, depth)}]"

    def _get_field_type_for_annotation(self, annotation, depth: int) -> str:
        origin = get_origin(annotation)
        if origin in {list, List}:
            list_item_type = get_args(annotation)[0]
            return self._format_list_type(list_item_type, depth)

        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            nested_schema = self._get_model_schema(annotation, depth)
            nested_indent = " " * 4 * (depth - 1)
            return f"{annotation.__name__}[\n{nested_schema}\n{nested_indent}]"

        return annotation.__name__
