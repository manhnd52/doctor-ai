import type { Meta, StoryObj } from "@storybook/react";
import SchemaGraph from "./SchemaGraph";

const meta = {
    title: "Components/SchemaGraph",
    component: SchemaGraph,
    decorators: [
        (Story) => (
            <div style={{ width: "100vw", height: "100vh" }}>
                <Story />
            </div>
        ),
    ],
    parameters: {
        layout: "fullscreen",
    },
} satisfies Meta<typeof SchemaGraph>;

export default meta;
type Story = StoryObj<typeof meta>;

// 1. Default schema (using the imported default schema)
export const Default: Story = {};

// 2. Custom schema story to demonstrate isolation and capability
export const CustomSchema: Story = {
    args: {
        schema: {
            nodes: [
                {
                    id: "User",
                    name: "User Node",
                    color: "#B6E3F4",
                    description: "Represents a user account in the system",
                    properties: [
                        { name: "userId", type: "string" },
                        { name: "email", type: "string" },
                        { name: "createdAt", type: "datetime" },
                    ],
                },
                {
                    id: "Post",
                    name: "Post Node",
                    color: "#68BDF6",
                    description: "Represents a blog post created by a user",
                    properties: [
                        { name: "postId", type: "string" },
                        { name: "title", type: "string" },
                        { name: "content", type: "string" },
                    ],
                },
                {
                    id: "Comment",
                    name: "Comment Node",
                    color: "#D66853",
                    description: "Represents a comment left on a post",
                    properties: [
                        { name: "commentId", type: "string" },
                        { name: "text", type: "string" },
                    ],
                },
            ],
            edges: [
                {
                    id: "User-CREATED_POST-Post",
                    name: "CREATED_POST",
                    source: "User",
                    target: "Post",
                    properties: [
                        { name: "timestamp", type: "datetime" },
                    ],
                },
                {
                    id: "User-COMMENTED_ON-Comment",
                    name: "COMMENTED_ON",
                    source: "User",
                    target: "Comment",
                    properties: [],
                },
                {
                    id: "Comment-BELONGS_TO-Post",
                    name: "BELONGS_TO",
                    source: "Comment",
                    target: "Post",
                    properties: [],
                },
            ],
        },
    },
};
