"""WebSocket consumers for real-time updates."""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import GenerationTask


class GenerationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time generation progress updates."""

    async def connect(self):
        """Handle WebSocket connection."""
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        self.task_group_name = f'generation_{self.task_id}'

        # Join task group
        await self.channel_layer.group_add(
            self.task_group_name,
            self.channel_name
        )

        await self.accept()

        # Send current task status
        task_data = await self.get_task_status()
        await self.send(text_data=json.dumps(task_data))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave task group
        await self.channel_layer.group_discard(
            self.task_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        # Request task status update
        task_data = await self.get_task_status()
        await self.send(text_data=json.dumps(task_data))

    async def task_progress(self, event):
        """Send task progress update to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'progress',
            'progress': event['progress'],
            'message': event['message'],
            'status': event.get('status', 'running')
        }))

    async def task_complete(self, event):
        """Send task completion to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'complete',
            'result': event['result'],
            'status': 'completed'
        }))

    async def task_error(self, event):
        """Send task error to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'error': event['error'],
            'status': 'failed'
        }))

    @database_sync_to_async
    def get_task_status(self):
        """Get current task status from database."""
        try:
            task = GenerationTask.objects.get(id=self.task_id)
            return {
                'type': 'status',
                'task_id': str(task.id),
                'status': task.status,
                'progress': task.progress,
                'message': task.progress_message,
                'result': task.result_data if task.status == 'completed' else None,
                'error': task.error_message if task.status == 'failed' else None
            }
        except GenerationTask.DoesNotExist:
            return {
                'type': 'error',
                'error': 'Task not found',
                'status': 'failed'
            }
